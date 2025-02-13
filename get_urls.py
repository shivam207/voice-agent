from typing import List, Dict, Union
import requests
from concurrent.futures import ThreadPoolExecutor, as_completed
from requests.exceptions import RequestException
import logging
from urllib.parse import urlparse
from markdownify import markdownify as md
import json

import html2text
from typing import Optional, Union
from bs4 import BeautifulSoup
import re
import codecs

class HTMLToMarkdownConverter:
    def __init__(self, 
                 body_width: int = 0,
                 ignore_links: bool = False,
                 ignore_images: bool = False,
                 ignore_tables: bool = False,
                 protect_links: bool = True,
                 unicode_snob: bool = False):
        """
        Initialize the HTML to Markdown converter with customizable options.
        
        Args:
            body_width (int): Width of the body text. 0 means no wrapping.
            ignore_links (bool): If True, ignore converting links
            ignore_images (bool): If True, ignore converting images
            ignore_tables (bool): If True, ignore converting tables
            protect_links (bool): If True, protect links from line wrapping
            unicode_snob (bool): If True, use Unicode characters instead of ASCII
        """
        self.converter = html2text.HTML2Text()
        self.converter.body_width = body_width
        self.converter.ignore_links = ignore_links
        self.converter.ignore_images = ignore_images
        self.converter.ignore_tables = ignore_tables
        self.converter.protect_links = protect_links
        self.converter.unicode_snob = unicode_snob
        
    def clean_html(self, html: str) -> str:
        """
        Clean HTML before conversion by removing unnecessary elements and normalizing content.
        
        Args:
            html (str): Raw HTML content
            
        Returns:
            str: Cleaned HTML content
        """
        # Parse HTML with BeautifulSoup
        soup = BeautifulSoup(html, 'html.parser')
        
        # Remove script and style elements
        for script in soup(["script", "style"]):
            script.decompose()
            
        # Remove comments
        for comment in soup.find_all(string=lambda text: isinstance(text, str) and '<!--' in text):
            comment.extract()
            
        # Remove empty paragraphs
        for p in soup.find_all('p'):
            if len(p.get_text(strip=True)) == 0:
                p.decompose()
                
        return str(soup)
    
    def post_process_markdown(self, markdown: str) -> str:
        """
        Clean up the converted markdown content.
        
        Args:
            markdown (str): Raw markdown content
            
        Returns:
            str: Cleaned markdown content
        """
        # Remove multiple consecutive blank lines
        markdown = re.sub(r'\n{3,}', '\n\n', markdown)
        
        # Remove trailing whitespace
        markdown = '\n'.join(line.rstrip() for line in markdown.splitlines())
        
        # Ensure single newline at end of file
        markdown = markdown.rstrip() + '\n'
        
        return markdown
    
    def convert(self, html: str, clean: bool = True) -> str:
        """
        Convert HTML to Markdown.
        
        Args:
            html (str): HTML content to convert
            clean (bool): Whether to clean the HTML before conversion
            
        Returns:
            str: Converted markdown content
            
        Raises:
            ValueError: If input HTML is empty or invalid
        """
        if not html or not isinstance(html, str):
            raise ValueError("Input HTML must be a non-empty string")
            
        try:
            # Clean HTML if requested
            if clean:
                html = self.clean_html(html)
                
            # Convert to markdown
            markdown = self.converter.handle(html)
            
            # Post-process the markdown
            markdown = self.post_process_markdown(markdown)
            
            return markdown
            
        except Exception as e:
            raise ValueError(f"Error converting HTML to Markdown: {str(e)}")

def html_to_markdown(html: str, 
                    body_width: int = 0,
                    ignore_links: bool = False,
                    ignore_images: bool = False,
                    ignore_tables: bool = False,
                    clean: bool = True) -> str:
    """
    Convenience function to convert HTML to Markdown.
    
    Args:
        html (str): HTML content to convert
        body_width (int): Width of the body text. 0 means no wrapping.
        ignore_links (bool): If True, ignore converting links
        ignore_images (bool): If True, ignore converting images
        ignore_tables (bool): If True, ignore converting tables
        clean (bool): Whether to clean the HTML before conversion
        
    Returns:
        str: Converted markdown content
    """
    converter = HTMLToMarkdownConverter(
        body_width=body_width,
        ignore_links=ignore_links,
        ignore_images=ignore_images,
        ignore_tables=ignore_tables
    )
    return converter.convert(html, clean=clean)


def fetch_urls(urls: List[str], timeout: int = 30, max_workers: int = 5) -> Dict[str, Union[str, str]]:
    """
    Fetch HTML content from multiple URLs concurrently.
    
    Args:
        urls (List[str]): List of URLs to fetch
        timeout (int): Request timeout in seconds
        max_workers (int): Maximum number of concurrent workers
        
    Returns:
        Dict[str, Union[str, str]]: Dictionary with URLs as keys and either HTML content
        or error messages as values
    """
    
    def validate_url(url: str) -> bool:
        """Validate URL format"""
        try:
            result = urlparse(url)
            return all([result.scheme, result.netloc])
        except Exception:
            return False

    def fetch_single_url(url: str) -> tuple[str, Union[str, str]]:
        """Helper function to fetch a single URL"""
        if not validate_url(url):
            return url, f"Invalid URL format: {url}"
            
        try:
            headers = {
                'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
            }
            
            response = requests.get(url, timeout=timeout, headers=headers)
            response.raise_for_status()
            
            # Check if content type is HTML
            content_type = response.headers.get('content-type', '').lower()
            if 'text/html' not in content_type:
                return url, f"Not an HTML page. Content-Type: {content_type}"
                
            return url, response.text
            
        except requests.exceptions.Timeout:
            return url, f"Timeout error after {timeout} seconds"
        except requests.exceptions.TooManyRedirects:
            return url, "Too many redirects"
        except requests.exceptions.SSLError:
            return url, "SSL verification failed"
        except requests.exceptions.HTTPError as e:
            return url, f"HTTP error occurred: {e.response.status_code}"
        except RequestException as e:
            return url, f"Error fetching URL: {str(e)}"
        except Exception as e:
            return url, f"Unexpected error: {str(e)}"

    # Remove duplicates and None values
    urls = list(filter(None, set(urls)))
    
    if not urls:
        return {}

    results = {}
    
    # Use ThreadPoolExecutor for concurrent fetching
    with ThreadPoolExecutor(max_workers=min(max_workers, len(urls))) as executor:
        future_to_url = {executor.submit(fetch_single_url, url): url for url in urls}
        
        for future in as_completed(future_to_url):
            url, result = future.result()
            results[url] = result
            
    return results

# def

# Example usage:
if __name__ == "__main__":
    test_urls = [
        "https://wise.com/help/articles/2452305/how-can-i-check-the-status-of-my-transfer",
        "https://wise.com/help/articles/2941900/when-will-my-money-arrive",
        "https://wise.com/help/articles/2977950/why-does-it-say-my-transfers-complete-when-the-money-hasnt-arrived-yet",
        "https://wise.com/help/articles/2977951/why-do-some-transfers-take-longer",
        "https://wise.com/help/articles/2932689/what-is-a-proof-of-payment",
        "https://wise.com/help/articles/2977938/whats-a-banking-partner-reference-number"
    ]
    
    results = fetch_urls(test_urls)
    
    md_results = {}
    for url, content in results.items():
        if isinstance(content, str) and content.startswith("Error"):
            print(f"Failed to fetch {url}: {content}")
        else:
            print(f"Successfully fetched {url}: {len(str(content))} characters")

        md_results[url] = md(content)
        # print (md_results[url])
        # Using the convenience function
        # markdown = html_to_markdown(content)
        # print("Using convenience function:")
        # print(markdown)

    md_string = json.dumps(md_results, ensure_ascii=False).encode('utf8')

    # with open('md.txt', 'w', encoding='utf-8') as f:
    #     f.write(md_string)

    with open('md.txt', 'wb') as f:
        f.write(md_string)

    
    
