# @DosTitulos 

Code for twitter bot [@DosTitulos](https://twitter.com/DosTitulos), it gets two titles from Google News and combines them into one new title.

Based on [@TwoHeadlines](https://twitter.com/TwoHeadlines), a bot by [Darius Kazemi](https:/twitter.com/tinysubversions). TwoHeadlines js code [here](https://github.com/dariusk/twoheadlines).

My bot is written in Python and some functionality was added to the original code.

## How it works

It randomly selects one of the categories from the sidebar of Google News Argentina, then it picks a topic on that category.
It selects a second category, different from the first and picks a topic on that category. It checks the titles on that category seeing if they are valid (in Spanish, not used recently, it contains the topic as part of the title text and that the title isn't truncated). From the valid titles it selects one randomly.
On the selected title the second topic is replaced with the first topic and the new title is sent to Twitter.
Other checks are done to avoid using the same topics or titles that where used on recent tweets.

Libraries used:
* [lxml](http://lxml.de/) to scrape the titles from Google News
* [guess_language](https://bitbucket.org/spirit/guess_language) to check that the title is in Spanish, sometimes Google shows titles on other languages
* [tweepy](http://www.tweepy.org/) to post the result to twitter



