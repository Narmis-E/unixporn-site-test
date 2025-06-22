#!/usr/bin/env python3
"""
Reddit r/unixporn Post Fetcher

This script fetches media from r/unixporn posts and organizes them into directories.
It creates user directories and post subdirectories as needed.
"""

import os
import re
import json
import requests
import praw
from urllib.parse import urlparse
from pathlib import Path
import argparse
import logging
from typing import List, Dict, Optional, Tuple

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

class UnixpornFetcher:
    def __init__(self, client_id: str, client_secret: str, user_agent: str):
        """Initialize the fetcher with Reddit API credentials."""
        self.reddit = praw.Reddit(
            client_id=client_id,
            client_secret=client_secret,
            user_agent=user_agent
        )
        self.base_dir = Path("rices")
        self.base_dir.mkdir(exist_ok=True)
    
    def sanitize_filename(self, filename: str) -> str:
        """Sanitize filename for filesystem compatibility."""
        # Remove/replace invalid characters
        filename = re.sub(r'[<>:"/\\|?*]', '', filename)
        filename = re.sub(r'[\[\]]', '', filename)  # Remove brackets
        filename = filename.strip()
        # Limit length
        if len(filename) > 100:
            filename = filename[:100]
        return filename or "untitled"
    
    def download_file(self, url: str, filepath: Path) -> bool:
        """Download a file from URL to filepath."""
        try:
            headers = {
                'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
            }
            response = requests.get(url, headers=headers, stream=True, timeout=30)
            response.raise_for_status()
            
            filepath.parent.mkdir(parents=True, exist_ok=True)
            
            with open(filepath, 'wb') as f:
                for chunk in response.iter_content(chunk_size=8192):
                    f.write(chunk)
            
            logger.info(f"Downloaded: {filepath}")
            return True
            
        except Exception as e:
            logger.error(f"Failed to download {url}: {e}")
            return False
    
    def extract_media_urls(self, submission) -> List[Tuple[str, str]]:
        """Extract media URLs from a Reddit submission."""
        media_urls = []
        
        # Check if it's a gallery post
        if hasattr(submission, 'is_gallery') and submission.is_gallery:
            if hasattr(submission, 'media_metadata'):
                for item_id, item in submission.media_metadata.items():
                    if 's' in item and 'u' in item['s']:
                        # Get the highest resolution image
                        url = item['s']['u'].replace('&amp;', '&')
                        extension = url.split('.')[-1].split('?')[0]
                        media_urls.append((url, extension))
        
        # Check for direct image/video links
        elif submission.url:
            url = submission.url
            parsed = urlparse(url)
            
            # Direct image/video
            if any(url.lower().endswith(ext) for ext in ['.jpg', '.jpeg', '.png', '.gif', '.mp4', '.webm']):
                extension = url.split('.')[-1].split('?')[0]
                media_urls.append((url, extension))
            
            # Reddit hosted images
            elif 'i.redd.it' in url:
                extension = url.split('.')[-1].split('?')[0]
                media_urls.append((url, extension))
            
            # Reddit hosted videos
            elif 'v.redd.it' in url:
                # For v.redd.it, we need to construct the video URL
                if hasattr(submission, 'media') and submission.media:
                    if 'reddit_video' in submission.media:
                        video_url = submission.media['reddit_video']['fallback_url']
                        media_urls.append((video_url, 'mp4'))
            
            # Imgur links
            elif 'imgur.com' in url:
                # Handle imgur direct links and albums
                if '/a/' in url or '/gallery/' in url:
                    logger.warning(f"Imgur albums not fully supported: {url}")
                else:
                    # Try to get direct image URL
                    if not any(url.lower().endswith(ext) for ext in ['.jpg', '.jpeg', '.png', '.gif']):
                        url += '.jpg'  # Try adding .jpg extension
                    extension = url.split('.')[-1].split('?')[0]
                    media_urls.append((url, extension))
        
        return media_urls
    
    def create_post_directory(self, username: str, post_title: str) -> Path:
        """Create directory structure for a post."""
        user_dir = self.base_dir / self.sanitize_filename(username)
        
        # Check if user already has posts
        existing_posts = []
        if user_dir.exists():
            existing_posts = [d for d in user_dir.iterdir() if d.is_dir()]
        
        # If user has multiple posts, create subdirectory
        if len(existing_posts) > 0 or self.user_has_multiple_posts(username):
            post_dir = user_dir / self.sanitize_filename(post_title)
        else:
            post_dir = user_dir
        
        post_dir.mkdir(parents=True, exist_ok=True)
        return post_dir
    
    def user_has_multiple_posts(self, username: str) -> bool:
        """Check if user has multiple posts (simplified check)."""
        # This is a simplified implementation
        # In practice, you might want to check your existing data or Reddit history
        return False
    
    def create_rice_metadata(self, submission, post_dir: Path, media_files: List[str]) -> Dict:
        """Create metadata JSON for the rice."""
        metadata = {
            "username": submission.author.name if submission.author else "[deleted]",
            "title": submission.title,
            "post_id": submission.id,
            "url": f"https://reddit.com{submission.permalink}",
            "created_utc": submission.created_utc,
            "score": submission.score,
            "num_comments": submission.num_comments,
            "media_files": media_files,
            "selftext": submission.selftext if submission.selftext else "",
        }
        
        metadata_file = post_dir / "metadata.json"
        with open(metadata_file, 'w', encoding='utf-8') as f:
            json.dump(metadata, f, indent=2, ensure_ascii=False)
        
        return metadata
    
    def fetch_post(self, post_url: str) -> Optional[Dict]:
        """Fetch a single post and its media."""
        try:
            # Extract post ID from URL
            post_id_match = re.search(r'/comments/([a-zA-Z0-9]+)', post_url)
            if not post_id_match:
                logger.error(f"Could not extract post ID from URL: {post_url}")
                return None
            
            post_id = post_id_match.group(1)
            submission = self.reddit.submission(id=post_id)
            
            logger.info(f"Fetching post: {submission.title}")
            
            # Extract media URLs
            media_urls = self.extract_media_urls(submission)
            
            if not media_urls:
                logger.warning(f"No media found in post: {post_url}")
                return None
            
            # Create directory structure
            username = submission.author.name if submission.author else "deleted_user"
            post_dir = self.create_post_directory(username, submission.title)
            
            # Download media files
            downloaded_files = []
            for i, (url, extension) in enumerate(media_urls):
                filename = f"image_{i+1:02d}.{extension}" if len(media_urls) > 1 else f"image.{extension}"
                filepath = post_dir / filename
                
                if self.download_file(url, filepath):
                    downloaded_files.append(filename)
            
            if not downloaded_files:
                logger.error(f"Failed to download any media for post: {post_url}")
                return None
            
            # Create metadata
            metadata = self.create_rice_metadata(submission, post_dir, downloaded_files)
            
            logger.info(f"Successfully processed post: {submission.title}")
            logger.info(f"Downloaded {len(downloaded_files)} files to: {post_dir}")
            
            return metadata
            
        except Exception as e:
            logger.error(f"Error fetching post {post_url}: {e}")
            return None

def main():
    parser = argparse.ArgumentParser(description='Fetch r/unixporn posts and media')
    parser.add_argument('post_url', help='Reddit post URL')
    parser.add_argument('--client-id', required=True, help='Reddit API client ID')
    parser.add_argument('--client-secret', required=True, help='Reddit API client secret')
    parser.add_argument('--user-agent', default='unixporn-fetcher/1.0', help='User agent string')
    
    args = parser.parse_args()
    
    fetcher = UnixpornFetcher(
        client_id=args.client_id,
        client_secret=args.client_secret,
        user_agent=args.user_agent
    )
    
    result = fetcher.fetch_post(args.post_url)
    
    if result:
        print(f"✅ Successfully processed post: {result['title']}")
        print(f"📁 Files saved to: rices/{result['username']}/")
        print(f"📊 Score: {result['score']}, Comments: {result['num_comments']}")
    else:
        print("❌ Failed to process post")
        exit(1)

if __name__ == "__main__":
    main()

