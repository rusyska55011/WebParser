from root import TorSession, Parser


class DoRequests(TorSession):
    session_requests = 0
    parser = Parser

    def __init__(self, tor_session):
        super(DoRequests, self).__init__(tor_session)
        self.session = self.receive_session()
        self.start_tor()

    def __del__(self):
        self.close_tor()
