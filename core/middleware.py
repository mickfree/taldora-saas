import json
from django.contrib import messages
from django.utils.deprecation import MiddlewareMixin

class HtmxMessageMiddleware(MiddlewareMixin):
    """
    Middleware that intercepts HTMX requests and appends any pending Django messages
    as a JSON-serialized event in the HX-Trigger response header.
    This allows Alpine.js or other frontend scripts to display toasts dynamically
    without reloading the page.
    """
    def process_response(self, request, response):
        # Only process if it is an HTMX request
        if request.headers.get('HX-Request') == 'true':
            # Retrieve pending messages
            storage = messages.get_messages(request)
            toast_messages = []
            for message in storage:
                toast_messages.append({
                    'message': message.message,
                    'tags': message.tags,
                })
            
            if toast_messages:
                # Get the existing HX-Trigger header if it exists
                hx_trigger = response.get('HX-Trigger')
                
                # Payload containing the messages list
                event_data = {'show-toasts': toast_messages}
                
                if hx_trigger:
                    try:
                        # If the header is already a JSON object, parse and merge
                        existing_data = json.loads(hx_trigger)
                        if isinstance(existing_data, dict):
                            existing_data.update(event_data)
                            response['HX-Trigger'] = json.dumps(existing_data)
                        else:
                            # If it was a single event name string, convert to object syntax
                            response['HX-Trigger'] = json.dumps({hx_trigger: True, **event_data})
                    except json.JSONDecodeError:
                        # Fallback if JSON decoding fails
                        response['HX-Trigger'] = json.dumps({hx_trigger: True, **event_data})
                else:
                    # If there's no HX-Trigger header, create a new one
                    response['HX-Trigger'] = json.dumps(event_data)
        
        return response
