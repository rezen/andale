from celery.backends.rpc import RPCBackend
import kombu

class Backend(RPCBackend):

    Exchange = kombu.Exchange

    def __init__(self, app, connection=None, exchange=None, exchange_type=None,
                 persistent=None, serializer=None, auto_delete=True, **kwargs):
        kwargs['url'] = 'guest:guest@rabbitmq:5672'
        kwargs['exchange'] = "finally_cooking_with_gas"
        kwargs['exchange_type'] = 'direct'
        super().__init__(app, **kwargs)
        print("---------- HEYYYYY -------------------", self.oid)


    def store_result(self, task_id, result, state,
                     traceback=None, request=None, **kwargs):
        # print("034555------------------- ")
        # print(result)
        # print(request)
        routing_key, correlation_id = self.destination_for(task_id, request)
        # print("//// ROUTI " +  routing_key)
        return super().store_result(task_id, result, state, traceback, request, **kwargs)


    def destination_for(self, task_id, request):
        try:
            request = request or current_task.request
        except AttributeError:
            raise RuntimeError(
                f'RPC backend missing task request for {task_id!r}')
        return request.reply_to, request.correlation_id or task_id

    def _create_exchange(self, name, type='direct', delivery_mode=2):
        # uses direct to queue routing (anon exchange).
        return self.Exchange("finally_cooking_with_gas")