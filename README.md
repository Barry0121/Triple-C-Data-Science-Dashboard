# Triple-C-Data-Science-Dashboard

Description of the dataset URL may be missing from early entries because it was not a capture group in early iterations. I made sure to not scrpae duplicate postings by checking whether I have scraped the url or not, so there may be duplicate postings because their URL changed. You can check if there are duplicate post IDs as I believe those are unique. Features columns represents null values as an empty array or may contain random features that is not releavant (could also be a null entry). Description could be empty or none. Null values for num_beds, sqft, num_baths, and price are expressed as -1. Address null values are expressed as None. Post_date, post_id, and post_url null values are expressed as None.

For entires before 8933, scrape date = post_date as it was not previously recorded.

Scrapped.csv includes all of the links that are already scrapped to prevent duplicate scraping

Scrape_log.txt includes all of the dates of the scrapping process
