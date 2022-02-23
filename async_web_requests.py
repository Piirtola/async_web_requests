from typing import Dict, List
import aiohttp
from aiohttp import client_exceptions
import asyncio
import time
import datetime

"""
Usage:
    Use this program from another file using the following:
     - import async_web_requests
     - results = async_web_requests.main_loop(urls_list, output=bool)
     
"""


# Credits given when credits are due...
# The code here is a bit modified version from a StackOverFlow post's answer:
# 		https://stackoverflow.com/questions/64335959/how-to-avoid-error-429-too-many-requests-python-with-asyncio


# TODO: I think I could simplify this a bit...
# TODO: I think this could benefit from being a object, didn't think about it when I started...
# TODO: Make a logger.


async def fetch(session: aiohttp.ClientSession, task: dict, output=False):
    """
    Fetches one item using URL to the site.
    This function should be used from an asychronous function loop...

    Parameters
    ----------
    task:
        in a format
        {
                    "url": Str to a site
                    "result": None
                    "status": int
            }
    output:
            True if any printable output is needed.
    """

    try:
        async with session.get(task["url"]) as response:
            # Correct status.
            if response.status == 200:
                text = await response.text()

            # Gone status. Still taking the text...
            elif response.status == 410:
                text = await response.text()

            # Not found.
            elif response.status == 404:
                text = "not found"

            # Forbidden status.
            elif response.status == 403:
                text = "forbidden"
                # Small await, for some reason :D?
                await asyncio.sleep(0.01)
            # Sometimes status not in any of the above. Hence this.
            else:
                text = "unknown"

            task["result"] = text
            task["status"] = response.status
            task["datetime"] = datetime.datetime.now()
    except asyncio.CancelledError:
        # Just marking the task as new so it will be fetched again, as this error means that
        # the fetch_all(...) has been stoped, for too many Forbidden codes in a row.
        # The stop helps to get rid of the code faster.
        task["result"] = None
        task["status"] = "new"
    # Is this a real concern?
    except client_exceptions.ClientOSError:
        task["result"] = None
        task["status"] = "forbidden"
    except asyncio.TimeoutError:
        task["result"] = None
        task["status"] = "forbidden"


async def fetch_all(
    session: aiohttp.ClientSession,
    urls: List[str],
    output=False,
    task_per_second: int = 1000,
    forbidden_max: int = 10,
    output_number: int = 100,
):
    """
    Fetches multiple sites using a list of URLs given as a parameter.
    Handles error code 403 (forbidden) in order to fetch sites that do not want to be scrapped too quicky
    Handles unvalid URLs to some extend, etc.

    Parameters
    ----------
    urls:
            A list containing URLs to sites from which the data will be collected.
    task_per_second:
            How many tasks the fetcher should try per second, some sites are good to scrap with a low task_per_second number
            as these sites do not want to be scrapped, lol. But most sites benefit from 1000 or more,
            i.e., low for heterogenous sites, possibly high for homogenous sites!
    output:
            True if any printable output is needed.
    forbidden_max:
            A number telling how many forbidden responses can come, before the sleeping.


    - Pretty slow on some sites, e.g.,
            If a site can have about 2500 requests done in a 1 minute. It will take super long time scrap 25k, different
            urls from that site. As the site will keep giving 403 error codes. The 403 handling isn't good, but it works.
            It doesn't break and keeps trying to fetch all those sites. It just waits for arbitrary time to before trying
            again, lol it works, so it's not that bad. Respecting the sites owner (only use for education purposes!)

    """

    start = time.perf_counter()
    if output is True:
        print("Starting to fetch URLs...")
        print(f"Total URLs: {len(urls)}")

    url_tasks = [
        {"url": url, "result": None, "status": "new", "datetime": None} for url in urls
    ]
    tasks_total = len(url_tasks)

    pos = 0
    while True:
        if pos % 100 == 0 or pos == 0:
            start2 = time.perf_counter()
        tasks_forbidden = len([i for i in url_tasks if i["status"] in [403]])

        if tasks_forbidden > forbidden_max:
            if output is True:
                print(f"{forbidden_max} or more forbidden responses!")
                print("Stopping now...")
            # Sleep for some reason?
            await asyncio.sleep(2)
            break

        # fetch = currently fetching
        tasks_running = len([i for i in url_tasks if i["status"] in ["fetch"]])
        # new = not yet fetched successfully
        tasks_waiting = len([i for i in url_tasks if i["status"] == "new"])

        # New fetch task if condition is met
        if pos < tasks_total and tasks_running < task_per_second:
            current_task = url_tasks[pos]
            current_task["status"] = "fetch"
            asyncio.create_task(fetch(session, current_task))
            pos += 1

        # Output on every Xth URL
        if pos % output_number == 0 and output == 0:
            print("Done tasks: {...}")
            print(f"Scheduled tasks: {pos}")
            print(f"Running now {tasks_running}")
            print(f"Remaining tasks: {tasks_waiting}")
            print(f"Time taken for {pos} URLs: {time.perf_counter() - start}")
            print()

        if tasks_running >= task_per_second:
            if output == 0:
                print("Throttling (2s)...")
            await asyncio.sleep(2)

        # If still waiting or running tasks, keep loop running.
        if tasks_waiting != 0 or tasks_running > 0:
            await asyncio.sleep(0.01)
        else:
            await asyncio.sleep(5)
            break

    """
	# TODO: Does this have any real effect on the program :D?
	#  Like why would it really have any effect...?
	# Graceful shutdown, needs to run the tasks that are still running
	# Does this really do anything :D???
	"""
    running_now = asyncio.all_tasks()
    asyncio.gather(*running_now)

    return url_tasks


async def fetcher(
    urls: List[str],
    output=False,
    task_per_second: int = 1000,
    forbidden_max: int = 10,
    output_number: int = 100,
):
    """
    Main function to run the programs here with default parameters, etc...
    I don't think that this is even a nessecary function?

    Parameters
    ----------
    urls: A list containing urls to be fetch.
                    A list containing URLs to sites from which the data will be collected.
    task_per_second:
            How many tasks the fetcher should try per second, some sites are good to scrap with a low task_per_second number
            as these sites do not want to be scrapped, lol. But most sites benefit from 1000 or more,
            i.e., low for heterogenous sites, possibly high for homogenous sites!
    output:
            True if any printable output is needed.
    forbidden_max:
            A number telling how many forbidden responses can come, before the sleeping.
    """

    async with aiohttp.ClientSession() as session:
        results = await fetch_all(
            session, urls, output, task_per_second, forbidden_max, output_number
        )

    return results


def main_loop(urls: list, output=False):
    """
    Main loop that fetches the data, from a list of URLs.
    Tries to handle the 403 errors as well as its possible...

    TODO: add params...
    """
    start = time.perf_counter()

    task_results = []
    pos = 0
    sleep_min = 5
    if output is True:
        print("Starting main_loop asynch web requests...")
        print("Total tasks:", len(urls))
        print()

    while True:
        start2 = time.perf_counter()
        pos += 1

        # Run the main fetcher function
        results = asyncio.get_event_loop().run_until_complete(
            fetcher(urls, output=output)
        )
        # Append those with code any other than 403 or 'new'
        [
            task_results.append(result)
            for result in results
            if result["status"] != 403 and result["status"] != "new"
        ]

        if output is True:
            __print_fetched(results, task_results, start, start2)

        # forbidden_list = get_forbidden_results(results)
        urls = __get_forbidden_and_new_urls(results)
        if len(urls) == 0:
            break

        if output is True:
            print(f"Forbidden on {len(urls)}, trying again...")
            print(f"Time passed: {time.perf_counter() - start}")
            print(f"Time passed this lap: {time.perf_counter() - start2}")
            sleeper(sleep_min, True)
            print()
        else:
            sleeper(sleep_min, False)

    return task_results


def __get_results_by_code(code, results) -> list:
    """
    Get a list of results filtered from results dict, using code.
    """
    return [i for i in results if i["status"] == code]


def __get_forbidden_and_new_urls(results):
    urls = [i["url"] for i in results if i["status"] == 403 or i["status"] == "new"]
    return urls


def __print_fetched(results, task_results, start, start2):
    codes = [200, 403, 410, 404]
    print(f"This lap time: {time.perf_counter() - start2}")
    for code in codes:
        code_results = __get_results_by_code(code, results)
        print(f"Code: {code}...")
        print("      ", len(code_results))
    print(f"Done now in total: {len(task_results)}")
    print(f"Time {time.perf_counter() - start}")


def sleeper(minutes: int = 5, output=True):
    for i in range(minutes):
        if output is True:
            print(f"Sleeping for {minutes - i} minutes...")
        time.sleep(60)
    if output is True:
        print("Sleeping done...")


if __name__ == "__main__":
    exit(
        f"This program ({__file__}) should be used via the main_loop function it contains, thus, don't directly run the file!"
        f"\nSee the file for more details..."
    )
