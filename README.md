# async_web_requests
Contains a program that enables one to get data from multiple URLs. Handles error code 403 if a site prevents one from requesting data rapidly.

### Usage:
  Use this program from another file using the following:
  
    - import async_web_requests
    - results = async_web_requests.main_loop(urls_list, output=bool)

### Dependencies
  - aiohttp
  - asyncio
