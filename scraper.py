import requests
from bs4 import BeautifulSoup
from googleapiclient.discovery import build
import time
from urllib.parse import urljoin
import os 
import pandas as pd

# phrases you want to search, edit this!
phrases = ["toronto property management"]

# setup static variables
api_key = os.environ['GSEARCH_KEY']
engine_id = '000530694050147109132:mcicvojownq'
country_code = "ca"

# Google Search Class object definition
# Allows you to auth with API, perform search, grab links from first 10 pages
class Google_Search(object):
    service = build("customsearch", "v1",
                    developerKey=api_key)

    def __init__(self, query):
        cse = Google_Search.service.cse()
        self.q = query
        self.cse = cse

    def pull_number_of_results(self):
        if not self.result:
            return False
        else:
            return self.result["searchInformation"]["totalResults"]

    def get_links(self):
        search_term = self.q
        cse = self.cse
        max_requests = 9
        links = []

        for i in range(0, max_requests):
            # This is the offset from the beginning to start getting the results from
            start_val = 1 + (i * 10)
            # Make an HTTP request object
            request = cse.list(q=search_term,
                num=10, #this is the maximum & default anyway
                start=start_val,
                cx=engine_id,
                gl=country_code
            )
            response = request.execute()
            results = response['items']
            for res in results:
                curr = res['link']
                links.append(curr)

        return links

# fn to return emails after searching for contact pages from base link
def search_link_for_emails(page_link):
    links = [page_link]
    contact_links = get_contact_links_from_link(page_link)
    links = links + contact_links
    
    email_name_pairs = []
    for link in links:
        emails, title_string = get_emails_from_link(link)
        if len(emails)>0:
            email_name_pairs.append((emails, title_string, link))

    return email_name_pairs

# fn to grab any contact links found in link
def get_contact_links_from_link(link):
    links = []
    soup = BeautifulSoup(requests.get(link).text, "lxml")
    for curr_link in soup.select("a[href*='about']"):
        links.append(urljoin(link, curr_link['href']))
    for curr_link in soup.select("a[href*='contact']"):
        links.append(urljoin(link, curr_link['href']))
    links = list(set(links))
    return links

# fn to only grab emails found on page
def get_emails_from_link(link):
    emails = []
    global num_emails
    global found_emails
    soup = BeautifulSoup(requests.get(link).text, "lxml")
    for email in soup.select("a[href^='mailto:']"):
        string = email['href']
        string = string.replace("mailto:", "")
        if string not in found_emails:
            emails.append(string)
            print(string)
            num_emails += 1
            found_emails.append(string)
    try:
        string = soup.title.string
    except:
        string = "Title not found."

    return emails, string

if __name__ == '__main__':

    #setup variables to keep track of progress
    num_emails = 0
    found_emails = []
    all_links = []

    #get all links from each query 
    print("Search phrases: " + str(phrases))
    for phrase in phrases:
        search_object = Google_Search(phrase)
        links = search_object.get_links()
        all_links = all_links + links

    # remove any duplicate links found
    all_links = list(set(all_links)) 
    print("Number of links " + str(len(all_links)))

    #go to each page, grabbing each email as (email, title of page, link to page)
    #all email triplets are stored in my_emails array
    my_emails = []
    for link in all_links:
        print(link)
        try:
            email_name_pairs = search_link_for_emails(link)
        except:
            email_name_pairs = []
        my_emails = my_emails + email_name_pairs
    print("Number of emails :" + str(len(my_emails)))

    # save email data to csv, using pandas for convenience, can change to csvwriter
    df = pd.DataFrame(my_emails, columns=['emails', 'title', 'link'])
    df.to_csv(home + "/results.csv")

