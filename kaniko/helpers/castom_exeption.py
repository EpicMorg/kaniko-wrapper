class FailedBuild(Exception):
    def __init__(self, service_name):
        self.service_name = service_name
        self.message = f"Failed to build service '{service_name}'."
        super().__init__(self.message)

    def __str__(self):
        return self.message
