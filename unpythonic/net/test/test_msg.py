# -*- coding: utf-8; -*-

from ...syntax import macros, warn  # noqa: F401
from ...test.fixtures import session

# from ...syntax import macros, test  # noqa: F401
# from ...test.fixtures import session, testset
#
# from io import BytesIO, SEEK_SET
#
# from .fixtures import nettest
#
# from ..msg import encodemsg, MessageDecoder
# from ..util import bytessource, streamsource, socketsource

def runtests():
    # TODO: As of MacroPy 1.1.0b2, this test module crashes at macro expansion time
    # TODO: due to a MacroPy bug involving `bytes` literals.
    warn["This test module disabled due to https://github.com/azazel75/macropy/issues/26"]
    # with testset("sans-IO"):
    #     with testset("basic usage"):
    #         # Encode a message:
    #         rawdata = b"hello world"
    #         message = encodemsg(rawdata)
    #         # Decode a message:
    #         decoder = MessageDecoder(bytessource(message))
    #         test[decoder.decode() == b"hello world"]
    #         test[decoder.decode() is None]  # The message should have been consumed by the first decode.
    #
    #     # Decoding a message gets a whole message and only that message.
    #     with testset("decode robustness"):
    #         bio = BytesIO()
    #         bio.write(message)
    #         bio.write(b"junk junk junk")
    #         bio.seek(0, SEEK_SET)
    #         decoder = MessageDecoder(streamsource(bio))
    #         test[decoder.decode() == b"hello world"]
    #         test[decoder.decode() is None]
    #
    #     # - Messages are received in order.
    #     # - Any leftover bytes already read into the receive buffer by the previous decode
    #     #   are consumed *from the buffer* by the next decode. This guarantees it doesn't
    #     #   matter if the transport does not honor message boundaries (which is indeed the
    #     #   whole point of having this protocol).
    #     #     - Note this means that should you wish to stop receiving messages on a particular
    #     #       source, and resume reading a raw stream from it instead, you must manually prepend
    #     #       the final contents of the receive buffer (`decoder.get_buffered_data()`) to whatever
    #     #       data you later receive from that source (since that data has already been placed
    #     #       into the receive buffer, so it is no longer available at the source).
    #     #     - So it's recommended to have a dedicated channel to communicate using messages,
    #     #       e.g. a dedicated TCP connection on which all communication is done with messages.
    #     #       This way you don't need to care about the receive buffer.
    #     with testset("message ordering"):
    #         bio = BytesIO()
    #         bio.write(encodemsg(b"hello world"))
    #         bio.write(encodemsg(b"hello again"))
    #         bio.seek(0, SEEK_SET)
    #         decoder = MessageDecoder(streamsource(bio))
    #         test[decoder.decode() == b"hello world"]
    #         test[decoder.decode() == b"hello again"]
    #         test[decoder.decode() is None]
    #
    #     # Synchronization to message start is performed upon decode.
    #     # It doesn't matter if there is junk between messages (the junk is discarded).
    #     with testset("stream synchronization"):
    #         bio = BytesIO()
    #         bio.write(encodemsg(b"hello world"))
    #         bio.write(b"junk junk junk")
    #         bio.write(encodemsg(b"hello again"))
    #         bio.seek(0, SEEK_SET)
    #         decoder = MessageDecoder(streamsource(bio))
    #         test[decoder.decode() == b"hello world"]
    #         test[decoder.decode() == b"hello again"]
    #         test[decoder.decode() is None]
    #
    #     # Junk containing sync bytes (0xFF) does not confuse or hang the decoder.
    #     with testset("junk containing sync bytes"):
    #         bio = BytesIO()
    #         bio.write(encodemsg(b"hello world"))
    #         bio.write(b"\xff" * 10)
    #         bio.write(encodemsg(b"hello again"))
    #         bio.seek(0, SEEK_SET)
    #         decoder = MessageDecoder(streamsource(bio))
    #         test[decoder.decode() == b"hello world"]
    #         test[decoder.decode() == b"hello again"]
    #         test[decoder.decode() is None]
    #
    # with testset("with TCP sockets"):
    #     def server1(sock):
    #         decoder = MessageDecoder(socketsource(sock))
    #         data = decoder.decode()
    #         return data
    #     def client1(sock):
    #         sock.sendall(encodemsg(b"hello world"))
    #     test[nettest(server1, client1) == b"hello world"]
    #
    #     def server2(sock):
    #         decoder = MessageDecoder(socketsource(sock))
    #         data = decoder.decode()
    #         return data
    #     def client2(sock):
    #         sock.sendall(encodemsg(b"hello world"))
    #         sock.sendall(encodemsg(b"hello again"))
    #     test[nettest(server2, client2) == b"hello world"]
    #
    #     def server3(sock):
    #         decoder = MessageDecoder(socketsource(sock))
    #         data = []
    #         data.append(decoder.decode())
    #         data.append(decoder.decode())
    #         return data
    #     def client3(sock):
    #         sock.sendall(encodemsg(b"hello world"))
    #         sock.sendall(encodemsg(b"hello again"))
    #     test[nettest(server3, client3) == [b"hello world", b"hello again"]]

if __name__ == '__main__':  # pragma: no cover
    with session(__file__):
        runtests()
