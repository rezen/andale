import timeflake

def generate_id():
    return timeflake.random().uuid
