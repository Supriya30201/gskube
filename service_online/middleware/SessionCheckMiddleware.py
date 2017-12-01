from datetime import datetime
from core import views
from dateutil.parser import parse


class SessionCheckMiddleware(object):
    def process_request(self, request):
        if 'last_activity' in request.session:
            last_activity = parse(request.session['last_activity'])
            now = datetime.now()

            if (now - last_activity).seconds > 600:
                return views.logout(request, error_message="Session expired, please login again.")

            request.session['last_activity'] = now.isoformat()
            if request.path == '/':
                return views.load_dashboard(request)

        elif request.path != '/' and request.path != '/logout':
            return views.logout(request, error_message="Please login again.")
