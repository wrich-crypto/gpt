from flask import jsonify

class ErrorCode:
    SUCCESS = 0
    ERROR_INVALID_PARAMETER = -1
    ERROR_INTERNAL_SERVER = -2
    ERROR_CODE = -3
    ERROR_ACCOUNT_OR_PASSWORD = -4
    ERROR_ACCOUNT_EXISTED = -5
    ERROR_BALANCE = -6
    ERROR_UNKNOWN = -7

    @staticmethod
    def success(data=None):
        response_data = {'code': ErrorCode.SUCCESS, 'msg': 'Success'}
        if data:
            response_data.update({'data': data})
        return response_data

    @staticmethod
    def error(error_code, message=''):
        if message != '':
            return {'code': error_code, 'msg': message}

        if error_code == ErrorCode.ERROR_UNKNOWN:
            return {'code': ErrorCode.ERROR_UNKNOWN, 'msg': 'Unknown error'}
        elif error_code == ErrorCode.ERROR_INVALID_PARAMETER:
            return {'code': ErrorCode.ERROR_INVALID_PARAMETER, 'msg': 'Invalid parameter'}
        else:
            return {'code': ErrorCode.ERROR_UNKNOWN, 'msg': 'Unknown error'}

    @staticmethod
    def custom_error(error_code, error_message):
        return {'code': error_code, 'msg': error_message}

def error_response(error_code, message):
    return error_response(error_code=error_code, message=message)
