from exception_logger import create_logger

db = {'user': 'root', 
      'password':'nfltomlinson21', 
      'host':'localhost',
      'database':'scraped_data'}

table = 'scraper_errors'

col_mapping ={'time':'time',
             'logger':'logger_name',
             'exception_type':'exception_type',
             'exception_message': 'exception_message',
             'traceback':'traceback',
             'note':'note',
             'function': 'function'}
             
scraper_logger = create_logger('missing_series_log', db, table, col_mapping)
