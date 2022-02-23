# async_web_requests
Contains a program that enables one to get data from multiple URLs. Handles error code 403 if a site prevents one from requesting data rapidly. 

- Meant to be used for one site with multiple different URLs.
- Doesn't handle 403 for different sites in an optimized way
- Doens't validate the URLs in any way

### Usage:
  Use this program from another file using the following:
  
    - import async_web_requests
    - results = async_web_requests.main_loop(urls_list, output=bool)

### Dependencies
  - aiohttp
  - asyncio
