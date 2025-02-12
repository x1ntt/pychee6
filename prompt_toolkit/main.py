# from prompt_toolkit.shortcuts import input_dialog

# r = input_dialog(
#     title='Example dialog window',
#     text='Do you want to continue?\nPress ENTER to quit.').run()
# print (r)

from concurrent.futures import ThreadPoolExecutor, wait, FIRST_COMPLETED, ALL_COMPLETED
import time

def spider(page):
    time.sleep(page)
    print(f"crawl task{page} finished")
    return page

with ThreadPoolExecutor(max_workers=3) as t: 
    all_task = [t.submit(spider, page) for page in range(1, 3)]
    print('finished')
    print('finished2')
    t.shutdown(wait=False, cancel_futures=True)
    print('finished3')