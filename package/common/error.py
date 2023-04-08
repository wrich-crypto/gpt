class ErrorCode:
    SUCCESS = 0
    ERROR_UNKNOWN = -1
    ERROR_INVALID_PARAMETER = -2

    @staticmethod
    def success(data=None):
        response_data = {'code': ErrorCode.SUCCESS, 'msg': 'Success'}
        if data:
            response_data.update(data)
        return response_data

    @staticmethod
    def error(error_code):
        if error_code == ErrorCode.ERROR_UNKNOWN:
            return {'code': ErrorCode.ERROR_UNKNOWN, 'msg': 'Unknown error'}
        elif error_code == ErrorCode.ERROR_INVALID_PARAMETER:
            return {'code': ErrorCode.ERROR_INVALID_PARAMETER, 'msg': 'Invalid parameter'}
        else:
            return {'code': ErrorCode.ERROR_UNKNOWN, 'msg': 'Unknown error'}

    @staticmethod
    def custom_error(error_code, error_message):
        return {'code': error_code, 'msg': error_message}
