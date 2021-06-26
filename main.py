import os 
from dotenv import load_dotenv
from processor.connector import ga_connector
from processor.convertor import ga_convertor
from processor.connector import binotel_connector
from processor.convertor import binotel_convertor
from processor.worker import clickhouse_worker
from datetime import datetime


def ga(dims, metrcs, start_date, end_date, columns, database, table):    
    ga_request = ga_connector.GoogleAnaliticsResolver(
        os.getenv('GA_KEY_FILE_LOCATION'), os.getenv('GA_VIEW_ID'))
    ga_request.initialize_analyticsreporting()
    ga_request.request_body(dims, metrcs, start_date, end_date)
    ga_json = ga_request.get_report()
    ga_convert = ga_convertor.GoogleAnaliticsConvertor(ga_json, columns)
    ga_data = ga_convert.get_data()
    clickhouse = clickhouse_worker.ClickHouseResolver()
    clickhouse.connect_to_client(host=os.getenv('click_host'), 
                port=os.getenv('click_port'), database=database)
    ga_data = ga_data[columns]
    clickhouse.insert(table, ga_data)
    clickhouse.disconnect()

def binotel(start_day, end_day):
    binotel_resolv = binotel_connector.BinotelResolver(
        os.getenv('binotel_key'), os.getenv('binotel_secret'))
    binotel_resolv.set_body()
    start_day = int(datetime.timestamp(datetime.strptime(start_day, '%Y-%m-%d')))
    end_day = int(datetime.timestamp(datetime.strptime(end_day, '%Y-%m-%d')))
    data = binotel_resolv.incoming_calls_period(start_day, end_day)
    binotel_convert = binotel_convertor.BinotelConvertor(data)
    in_data = binotel_convert.incoming()
    clickhouse = clickhouse_worker.ClickHouseResolver()
    clickhouse.connect_to_client(host=os.getenv('click_host'), 
                    port=os.getenv('click_port'), database='client')
    clickhouse.insert('calls', in_data)
    data = binotel_resolv.calltracking_calls_period(start_day, end_day)
    binotel_convert = binotel_convertor.BinotelConvertor(data)
    in_data = binotel_convert.call_tracking()
    clickhouse.insert('calls', in_data)
    clickhouse.disconnect()

def main():
    load_dotenv('configuration/config.env')
    dims = ['ga:dimension2', 'ga:dateHourMinute', 
        'ga:source', 'ga:medium', 'ga:campaign','ga:country', 'ga:sessionCount']
    metrics = ['ga:avgSessionDuration']
    columns = ['ga_id', 'timestamp', 'source', 'medium', 'campaign', 'country', 'session_count','avg_session_duration']
    ga(dims, metrics, '2021-05-01', '2021-06-24', columns, 'client', 'browser')
    dims = ['ga:dimension2', 'ga:dimension1', 'ga:dateHourMinute', 
        'ga:source', 'ga:medium', 'ga:campaign','ga:country', 'ga:sessionCount']
    columns = ['ga_id', 'fb_id', 'timestamp', 'source', 'medium', 'campaign', 'country', 'session_count','avg_session_duration']
    ga(dims, metrics, '2021-06-25', 'today', columns, 'client', 'browser')
    binotel('2020-05-01', '2021-06-26')

if __name__ == '__main__':
    main()