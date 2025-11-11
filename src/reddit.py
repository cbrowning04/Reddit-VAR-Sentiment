"""Objects to scrape data from reddit using PRAW."""
# Standard Library
from copy import deepcopy
import datetime

# Third Party
import praw
import pandas as pd

# Local
from utils import _type_defence


class RedditScraper:
    """A class to scrape data from reddit."""

    def __init__(
            self,
            client_id: str,
            client_secret: str,
            user_agent: str = "Default Agent"
    ):
        # defences
        _type_defence(client_id, str, "client_id")
        _type_defence(client_secret, str, "client_secret")
        _type_defence(user_agent, str, "user_agent")
        # assign class attributes
        self.client_id = client_id
        self.client_secret = client_secret
        self.user_agent = user_agent
        self.scraped_data = {}
        self.posts_df = None
        self.comments_df = None
        self.joined_data_df = None
        self.edges = None
        self.nodes = None
        # connect to reddit API
        self.reddit = self._connect()

    def _connect(self):
        """Connect to reddit using the PRAW package."""
        reddit_obj = praw.Reddit(
            client_id=self.client_id,
            client_secret=self.client_secret,
            user_agent=self.user_agent,
        )
        return reddit_obj

    def _obtain_comments(self, post, current_comments: dict, comment_limit: int = 10) -> dict:
        """Fetch the comments from a post."""
        post.comments.replace_more(limit=0)
        for comment in post.comments.list()[:comment_limit]:
            current_comments["post_id"].append(post.id)
            current_comments["comment_id"].append(comment.id)
            current_comments["comment_content"].append(comment.body)
            current_comments["comment_author"].append(
                comment.author.name if comment.author else "unknown_author"
            )
            current_comments["comment_score"].append(comment.score)
            current_comments["comment_date"].append(datetime.datetime.fromtimestamp(comment.created))
        return current_comments

    def scrape_subreddit(
            self,
            subreddit: str,
            search: str,
            post_limit: int = 50,
            sort: str = "top",
            time_filter: str = "all",
            get_comments: bool = True,
            comment_limit: int = 10
    ) -> dict:
        # defences
        _type_defence(subreddit, str, "subreddit")
        _type_defence(search, str, "search")
        _type_defence(post_limit, int, "post_limit")
        _type_defence(sort, str, "sort")
        valid_sorts = ["relevance", "hot", "top", "new", "comments"]
        if sort not in valid_sorts:
            raise ValueError(f"Sort must be one of {valid_sorts}")
        _type_defence(time_filter, str, "time_filter")
        valid_time_filters = ["all", "day", "hour", "month", "week", "year"]
        if time_filter not in valid_time_filters:
            raise ValueError(f"Time filter must be one of {valid_time_filters}")
        _type_defence(get_comments, bool, "get_comments")
        _type_defence(comment_limit, int, "comment_limit")
        # scrape data
        sub = self.reddit.subreddit(subreddit)
        all_posts = {
            "post_id": [],
            "title": [],
            "author": [],
            "author_flair": [],
            "score": [],
            "upvote_ratio": [],
            "post_date": [],
            "comments": {
                "post_id": [],
                "comment_id": [],
                "comment_content": [],
                "comment_author": [],
                "comment_score": [],
                "comment_date": []
            }
        }
        results = sub.search(query=search, limit=post_limit, sort=sort, time_filter=time_filter)
        for post in results:
            all_posts["post_id"].append(post.id)
            all_posts["title"].append(post.title)
            all_posts["author"].append(
                post.author.name if post.author else "unknown_author"
            )
            all_posts["author_flair"].append(
                post.author_flair_text
            )
            all_posts["score"].append(post.score)
            all_posts["upvote_ratio"].append(post.upvote_ratio)
            all_posts["post_date"].append(datetime.datetime.fromtimestamp(post.created))
            # scrape comments if requested
            if get_comments:
                comments = self._obtain_comments(
                    post=post,
                    comment_limit=comment_limit,
                    current_comments=all_posts["comments"])
                all_posts["comments"] = comments
        # add scraped data to object attr
        try:
            self.scraped_data[subreddit][search] = all_posts
        except KeyError:
            self.scraped_data[subreddit] = {}
            self.scraped_data[subreddit][search] = all_posts
        # return raw data for current search
        subreddit_data = {subreddit: all_posts}
        return subreddit_data

    def multi_scrape(
        self,
        subreddits: list,
        search: str,
        post_limit: int = 50,
        sort: str = "top",
        time_filter: str = "all",
        get_comments: bool = True,
        comment_limit: int = 10
    ) -> dict:
        """Scrape multiple subreddits using the same query."""
        _type_defence(subreddits, list, "subreddit")
        if len(subreddits) <= 0:
            raise UserWarning("Can not scrape data as no subreddit was specified.")
        combined_data = {}
        for sub in subreddits:
            data = self.scrape_subreddit(
                subreddit=sub,
                search=search,
                post_limit=post_limit,
                sort=sort,
                time_filter=time_filter,
                get_comments=get_comments,
                comment_limit=comment_limit
            )
            combined_data[sub] = data[sub]
        return combined_data

    def semi_format_to_pandas(self) -> tuple:
        """Format scraped data into two pandas dataframes; posts and comments."""
        data_copy = deepcopy(self.scraped_data)
        if not data_copy:
            raise UserWarning("No data has been scraped.")
        posts_df = pd.DataFrame()
        comments_df = pd.DataFrame()
        for subr in data_copy:
            for query in data_copy[subr]:
                items = len(data_copy[subr][query]["post_id"])
                data_copy[subr][query]["subreddit"] = [subr for item in range(items)]
                data_copy[subr][query]["search_query"] = [query for item in range(items)]
                comments = data_copy[subr][query].pop("comments", None)
                comments_df = pd.concat([comments_df, pd.DataFrame(comments)], axis=0)
                posts_df = pd.concat([posts_df, pd.DataFrame(data_copy[subr][query])], axis=0)
        self.posts_df = posts_df
        self.comments_df = comments_df
        return posts_df, comments_df

    def full_format_to_pandas(self) -> pd.DataFrame:
        """Format scraped data into a pandas dataframe."""
        all_posts, all_comments = self.semi_format_to_pandas()
        all_posts.post_id = all_posts.post_id.astype("object")
        all_comments.post_id = all_comments.post_id.astype("object")
        joined_data_df = all_posts.merge(all_comments, how="right", on="post_id")
        self.joined_data_df = joined_data_df
        return joined_data_df

    def create_nodes_and_edges(self) -> tuple:
        """Reformat scraped data to be used in a social network analysis."""
        # make sure data is correctly formatted
        if self.joined_data_df is None:
            self.full_format_to_pandas()
        # reformat data into separate edges and nodes datasets
        copied_data = deepcopy(self.joined_data_df)
        # get nodes
        possible_users = list(copied_data.author) + list(copied_data.comment_author)
        nodes = list(set(possible_users))  # get unique
        nodes = pd.DataFrame({"id": nodes})
        # get edges
        copied_data.rename(
            columns={
                "comment_author": "source",
                "author": "target"
            },
            inplace=True
        )
        edges = copied_data
        return nodes, edges
