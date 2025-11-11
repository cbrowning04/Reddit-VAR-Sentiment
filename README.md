# Reddit VAR Sentiment

## Description
This repository contains a small amount of code used to understand the sentiment of reddit users towards VAR (Video Assistant Referee) technology.  

The main purpose of this analysis was for an applied data science bachelors degree dissertation. It is being held here for future reference.

##  Scraping Data
To obtain data in a similar fashion to this analysis (from reddit), the `RedditScraper` class can be used from [reddit.py](src/reddit.py).

This can be seen in the example below. Note that the provided code does not support loading environment variables in any way (e.g., .env file).

```python
# Create map of LeagueName=>Subreddit
subreddits = {
    "English Premier League": "PremierLeague",
    "La Liga (Spain)": "LaLiga",
    "Major League Soccer (USA)": "MLS",
    "Bundesliga (Germany)": "Bundesliga",
    "Serie A (Italy)": "seriea"
}

# Scrape the relevant data
results = scraper.multi_scrape(
    subreddits=list(subreddits.values()),
    search='("Video Assistant Referee" OR VAR)",
    post_limit=100,
    sort="relevance",
    time_filter="all",
    get_comments=True,
    comment_limit=15
)
```

