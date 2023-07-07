from threading import Lock


class TaskDependencySemaphore:
    """
    A semaphore that only allows to acquire a dependency if
    no tasks are using it.
    """

    def __init__(self, name=None, debug=False):
        self._acquire_task_release_lock = Lock()
        self._general_lock = Lock()
        self.locks = []
        self.to_release = 0
        self.name = name
        self.debug = debug

    def acquire_task(self, info=None):
        with self._acquire_task_release_lock:
            self.to_release += 1
            self._print(f'\nAcquired {self.name or ""} by {info}: {self.value}')

    def acquire_dependecy(self, info=None):
        with self._acquire_task_release_lock:
            self._print(f'\nDependency lock {self.name or ""} by {info}: {self.value}')
            if self.to_release == 0:
                return

            lock = Lock()
            self.locks.append(lock)
            lock.acquire()
        lock.acquire()

        self._print(f'\nDependency UNlock {self.name or ""} by {info}: {self.value}')

    def release_task(self, info=None):
        with self._acquire_task_release_lock:
            self.to_release = max(self.to_release - 1, 0)
            self._print(f'\nReleased {self.name or ""} by {info}: {self.value}')
            if self.to_release == 0:
                self._print(f'\nUnlocking {self.name or ""} by {info}: {self.value}')
                for lock in self.locks:
                    if lock.locked():
                        lock.release()
                self.locks.clear()

    def acquire(self, info=None):
        with self._general_lock:
            self.acquire_dependecy(info)
            self.acquire_task(info)

    def release(self, info=None):
        self.release_task(info)

    def _print(self, *args, **kwargs):
        if self.debug:
            print(*args, **kwargs)

    @property
    def value(self):
        return self.to_release
