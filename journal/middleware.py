from time import time
import logging


logger = logging.getLogger('journal')


class SimpleMiddleware:
    def __init__(self, get_response) -> None:
        self.get_response = get_response

    def __call__(self, request):
        # before view
        current_time = time()

        response = self.get_response(request) # call view

        # after view
        result_time = time() - current_time

        if result_time > .2 and not request.path.startswith(('/static/', '/media/')):
            logger.warning(f'path: "{request.get_full_path()}" - method: {request.method} - time: {result_time:.3f} - status_code: {response.status_code}')
        else:
            logger.info(f'path: "{request.get_full_path()}" - method: {request.method} - time: {result_time:.3f} - status_code: {response.status_code}')

        return response