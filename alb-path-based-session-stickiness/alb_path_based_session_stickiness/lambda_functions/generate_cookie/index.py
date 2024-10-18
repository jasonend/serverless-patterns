import json
import re
import requests
import datetime
import os
import logging

logger = logging.getLogger()
logger.setLevel(logging.INFO)

def lambda_handler(event, context):
    logger.info(f"Received event: {json.dumps(event)}")
    
    if event.get('path') == '/favicon.ico':
        logger.info("Favicon request received, returning 204 No Content")
        return {
            'statusCode': 204,
            'body': ''
        }

    try:
        path = event.get('path', '')
        logger.info(f"Processing path: {path}")
        
        try: 
            cookie_value = re.search(os.environ['PATH_REGEX'], path).group(1)
        except AttributeError:
            logger.warning(f"Regex match not found in path: {path}")
            cookie_value = path

        logger.info(f"Extracted cookie value: {cookie_value}")

        headers = event.get('multiValueHeaders', {})
        url = f"{headers.get('x-forwarded-proto', ['https'])[0]}://{headers.get('host')[0]}{path}"
        logger.info(f"Constructed URL: {url}")
        
        # Create cookie with the regex match
        custom_cookie = f'PATH_COOKIE={cookie_value}'
        
        proxy_headers = {
            'Cookie': custom_cookie,
        }
        
        method = event.get('httpMethod', 'GET')
        body = event.get('body', '')

        logger.info(f"Sending request to EC2: Method: {method}, URL: {url}, Headers: {proxy_headers}")
        response = requests.request(method, url, headers=proxy_headers, data=body, timeout=1)
        logger.info(f"Received response from EC2: Status: {response.status_code}, Headers: {dict(response.headers)}")

        # Prepare the response
        multi_value_headers = {}
        for key, value in response.headers.items():
            if key.lower() == 'set-cookie':
                # If there are multiple Set-Cookie headers, ensure they're all included
                if 'Set-Cookie' in multi_value_headers:
                    multi_value_headers['Set-Cookie'].append(value)
                else:
                    multi_value_headers['Set-Cookie'] = [value]
            else:
                # For non-Set-Cookie headers, always use a list
                multi_value_headers[key] = [value]

        # Add your custom cookie
        expiration = (datetime.datetime.now() + datetime.timedelta(minutes=30)).strftime('%a, %d %b %Y %H:%M:%S GMT')
        custom_cookie_with_attributes = f'{custom_cookie}; Expires={expiration}; Path={path}'
        if 'Set-Cookie' in multi_value_headers:
            multi_value_headers['Set-Cookie'].append(custom_cookie_with_attributes)
        else:
            multi_value_headers['Set-Cookie'] = [custom_cookie_with_attributes]

        logger.info(f"Preparing Lambda response: Status: {response.status_code}, Headers: {multi_value_headers}")
        return {
            'statusCode': response.status_code,
            'multiValueHeaders': multi_value_headers,
            'body': response.text
        }

    except requests.exceptions.Timeout:
        logger.error("Request to EC2 timed out")
        return {
            'statusCode': 504,
            'multiValueHeaders': {'Content-Type': ['application/json']},
            'body': json.dumps({'message': 'The endpoint did not respond within 1 second.'})
        }
    except requests.exceptions.RequestException as e:
        logger.error(f"Request to EC2 failed: {str(e)}")
        return {
            'statusCode': 502,
            'multiValueHeaders': {'Content-Type': ['application/json']},
            'body': json.dumps({'error': f'Request failed: {str(e)}'})
        }
    except Exception as e:
        logger.error(f"Unexpected error: {str(e)}")
        return {
            'statusCode': 500,
            'multiValueHeaders': {'Content-Type': ['application/json']},
            'body': json.dumps({'error': str(e)})
        }
