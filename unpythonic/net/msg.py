# -*- coding: utf-8; -*-
"""A simplistic message protocol.

This adds rudimentary message framing and stream re-synchronization on top of a
stream-based transport layer such as TCP.

**Technical details**

A message consists of a header and a body, where:

  header:
    0xFF: sync byte, start of new message
      Chosen because our primary payload target is utf-8 encoded text,
      where the byte 0xFF never appears.
    literal "v": start of protocol version field
    two bytes containing the protocol version, currently the characters "01" as utf-8.
      These don't need to be number characters, any Unicode codepoints below 127 will do.
      It's unlikely more than (127 - 32)**2 = 95**2 = 9025 backwards incompatible versions
      of this protocol will be ever needed, even in the extremely unlikely case this code
      ends up powering someone's 31st century starship.
    literal "l": start of message length field
    utf-8 string, containing the number of bytes in the message body
      In other words, `str(len(body)).encode("utf-8")`.
    literal ";": end of message length field (in v01, also the end of the header)
  body:
    arbitrary payload, exactly as many bytes as the header said.
"""

__all__ = ["sendmsg", "mkrecvbuf", "recvmsg"]

import select
from io import BytesIO

from ..collections import box, unbox

# TODO: make a sans-IO version of this. sendmsg is easy, but recvmsg needs a
# callback to retrieve more data from the underlying stream.
# https://sans-io.readthedocs.io/

def sendmsg(body, sock):
    """Send a message on a socket.

    body: Arbitrary data as a `bytes` object.
    sock: An open socket to send the data on.
    """
    buf = BytesIO()
    buf.write(b"\xff")  # sync byte
    buf.write(b"v01")  # message protocol version
    # message body length
    buf.write(b"l")
    buf.write(str(len(body)).encode("utf-8"))
    buf.write(b";")
    # message body
    buf.write(body)
    sock.sendall(buf.getvalue())

# SICP, data abstraction... no need for our caller to know the implementation
# details of our receive buffer.
def mkrecvbuf(initial_contents=b""):
    """Make a receive buffer object for use with `recvmsg`."""
    # The buffer is held inside an `unpythonic.collections.box`, because
    # `BytesIO` cannot be cleared, so when a complete message has been read,
    # any remaining data already read from the socket must be written into a
    # new BytesIO, which we then send into the box to replace the original one.
    return box(BytesIO(initial_contents))

def recvmsg(buf, sock):
    """Receive next message from socket, and update buffer.

    Returns the message body as a `bytes` object, or `None` if the socket was
    closed by the other end before a complete message was received.

    buf: A receive buffer created by `mkrecvbuf`. This is used as a staging
         area for incoming data, since we must hold on to data already received
         from the socket, but not yet consumed by inclusion into a complete
         message.

         Note it is the caller's responsibility to hold on to the receive buffer
         during a session; often, it will contain the start of the next message,
         which is needed for the next run of `recvmsg`.

    sock: An open socket to receive the data on.
    """
    class SocketClosedByPeer(Exception):
        pass
    class MessageParseError(Exception):
        pass

    def lowlevel_read():
        """Read some more data from socket, update receive buffer.

        Return the current contents of the receive buffer.

        Invariant: the identity of the `BytesIO` in the `buf` box
        does not change.
        """
        bio = unbox(buf)
        rs, ws, es = select.select([sock], [], [])
        for r in rs:
            data_in = sock.recv(4096)
            if len(data_in) == 0:
                raise SocketClosedByPeer
            bio.write(data_in)
            return bio.getvalue()
        assert False

    def synchronize():
        """Synchronize the stream to the start of a new message.

        This reads and discards data until the start of a new message is
        (potentially) found.

        After `synchronize()`, the sync byte `0xFF` is guaranteed to be
        in the receive buffer.

        **Usage note**:

        Utf-8 encoded text bodies are safe, but if the message body is binary,
        false positives may occur.

        To find out, call `read_header`; it will raise `MessageParseError`
        if a header cannot be parsed at the current position. Repeat the
        sequence of `synchronize` and `read_header` until a header is
        successfully parsed.
        """
        while True:
            val = lowlevel_read()
            if b"\xff" in val:
                j = val.find(b"\xff")
                junk, start_of_msg = val[:j], val[j:]  # noqa: F841
                # Discard previous BytesIO, start the new one with the 0xFF.
                buf << BytesIO(start_of_msg)
                return

    def read_header():
        """Parse message header from the incoming data.

        Return the message body length.

        If successful, drop the header from the receive buffer.
        """
        val = unbox(buf).getvalue()
        while len(val) < 5:
            val = lowlevel_read()
        # BEWARE: val[0] == 255, but val[0:1] == b"\xff".
        if val[0:1] != b"\xff":  # sync byte
            raise MessageParseError
        if val[1:4] != b"v01":  # protocol version 01
            raise MessageParseError
        if val[4:5] != b"l":  # length of body field
            raise MessageParseError
        while b";" not in val:  # end of length of body field
            val = lowlevel_read()
        j = val.find(b";")
        body_len = int(val[5:j].decode("utf-8"))
        buf << BytesIO(val[(j + 1):])
        return body_len

    def read_body(body_len):
        """Read and return message body.

        Drop the body from the receive buffer.
        """
        val = unbox(buf).getvalue()
        while len(val) < body_len:
            val = lowlevel_read()
        # Any leftovers belong to the next message.
        body, leftovers = val[:body_len], val[body_len:]
        buf << BytesIO(leftovers)
        return body

    # With these, receiving a message is as simple as:
    while True:
        try:
            synchronize()
            body_len = read_header()
            return read_body(body_len)
        except MessageParseError:  # just re-synchronize if the message could not be parsed.
            pass
        except SocketClosedByPeer:
            return None
