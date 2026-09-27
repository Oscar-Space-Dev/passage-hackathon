import uvicorn

if __name__ == '__main__':
    uvicorn.run('passage.main:app', host='127.0.0.1', port=8088, log_level='info', access_log=False)
