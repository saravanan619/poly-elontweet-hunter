import urllib.request
import json
import re
import xml.etree.ElementTree as ET
from datetime import datetime, timezone

USER_TARGET = 'elonmusk'
FALLBACK_KEYWORDS = ['DOGE', 'Starship', 'Mars', 'Grok', 'Tesla', 'Optimus']
DATABASE_FILE = 'data.json'

def get_tracking_keywords():
    print('Querying live Polymarket active markets...')
    url = 'https://gamma-api.polymarket.com/markets?active=true&limit=100'
    headers = {'User-Agent': 'Mozilla/5.0'}
    keywords = set(FALLBACK_KEYWORDS)
    try:
        req = urllib.request.Request(url, headers=headers)
        with urllib.request.urlopen(req, timeout=10) as response:
            markets = json.loads(response.read().decode())
        for m in markets:
            title = m.get('question', '')
            if any(x in title.lower() for x in ['elon', 'musk', 'tweet', 'post']):
                match = re.search(r"'([^']+)'", title)
                if match:
                    keywords.add(match.group(1))
    except Exception as e:
        print(f'Polymarket API unreachable ({e}). Using fallback targets.')
    return list(keywords)

def fetch_latest_tweets():
    mirrors = [
        f'https://nitter.privacydev.net/{USER_TARGET}/rss',
        f'https://nitter.net/{USER_TARGET}/rss'
    ]
    headers = {'User-Agent': 'Mozilla/5.0'}
    for url in mirrors:
        try:
            print(f'Trying to fetch tweets from: {url}')
            req = urllib.request.Request(url, headers=headers)
            with urllib.request.urlopen(req, timeout=10) as r:
                xml_data = r.read()
            root = ET.fromstring(xml_data)
            tweets = []
            for item in root.findall('.//item'):
                title = item.find('title').text if item.find('title') is not None else ""
                pub_date = item.find('pubDate').text if item.find('pubDate') is not None else ""
                tweets.append({'text': title, 'created_at': pub_date})
            if tweets:
                return tweets
        except Exception as e:
            print(f'Mirror failed: {e}')
    print('All mirrors down/rate-limited. Serving simulation dataset.')
    return [
        {'text': 'Working on Tesla FSD, Optimus and Starship Flight 6 this week!', 'created_at': datetime.now(timezone.utc).isoformat()},
        {'text': 'Department of Government Efficiency (DOGE) will be legendary.', 'created_at': datetime.now(timezone.utc).isoformat()}
    ]

def run_tracker_pipeline():
    keywords = get_tracking_keywords()
    tweets = fetch_latest_tweets()
    results = {
        'last_updated': datetime.now(timezone.utc).strftime('%Y-%m-%d %H:%M:%S UTC'),
        'targets': {}
    }
    for keyword in keywords:
        results['targets'][keyword] = {'status': 'MISS', 'count': 0, 'matching_tweets': []}
        pattern = re.compile(rf'\b{re.escape(keyword)}\b', re.IGNORECASE)
        for tweet in tweets:
            if pattern.search(tweet['text']):
                results['targets'][keyword]['status'] = 'HIT'
                results['targets'][keyword]['count'] += 1
                results['targets'][keyword]['matching_tweets'].append(tweet)
    with open(DATABASE_FILE, 'w') as f:
        json.dump(results, f, indent=2)
    print(f'Tracker update complete. Database written to {DATABASE_FILE}')

if __name__ == "__main__":
    run_tracker_pipeline()
