from sqlalchemy import func, select


GIT_LOCK = 42

# https://snippets.aktagon.com/snippets/927-how-to-use-postgresql-advisory-locks-with-sqlalchemy-and-python
def execute(session, lock_fn, lock_id, scope):
    """
    Executes the lock function
    """
    return session.execute(select(lock_fn(lock_id, scope))).scalar()


def obtain_lock(session, lock_id, scope):
    """
    Obtains the advisory lock
    """
    lock_fn = func.pg_try_advisory_lock
    return execute(session, lock_fn, lock_id, scope)


def release_lock(session, lock_id, scope):
    """
    Releases the advisory lock
    """
    lock_fn = func.pg_advisory_unlock
    return execute(session, lock_fn, lock_id, scope)


def with_lock(session, success_func, failure_func, lock_id, scope=1):
    """
    Executes success_func if the lock can be obtained, else failure_func.
    """
    obtained_lock = False
    try:
        obtained_lock = obtain_lock(session, lock_id, scope)
        if obtained_lock:
            success_func()
        else:
            failure_func()
    finally:
        if obtained_lock:
            release_lock(session, lock_id, scope)