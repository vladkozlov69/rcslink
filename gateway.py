"""The gateway to interact with a RCSLink port."""
import logging

from serial import SerialException
import serial_asyncio
import asyncio

# import sys, time, threading

from homeassistant.core import callback
from homeassistant.helpers.entity import Entity
from .const import DOMAIN


_LOG = logging.getLogger(__name__)
_LOG.setLevel(logging.DEBUG)

NO_RCSLINK_FOUND = "No RCSLink found"

class Gateway(Entity):
    """Gateway to interact with RCSLink."""
    _config_entry = None
    _sensor = None
    _serial_loop_task = None

    def __init__(self, config_entry, hass):
        """Initialize the sms gateway."""
        self._hass = hass
        self._config_entry = config_entry
        self._writer = None

        print('g1')

    async def async_added_to_hass(self):
        """Handle when an entity is about to be added to Home Assistant."""
        print('async_added_to_hass')
        self._serial_loop_task = self._hass.loop.create_task(
            self.serial_read(
                '/dev/tty.usbmodem14301',
                9600,
                serial_asyncio.serial.EIGHTBITS,
                serial_asyncio.serial.PARITY_NONE,
                serial_asyncio.serial.STOPBITS_ONE,
                False,
                False,
                False,
            )
        )

        print('g2')

        # asyncio.wait(self._serial_loop_task)
        # return await self._serial_loop_task

        # print('g3')
 

    async def serial_read(
        self,
        device,
        baudrate,
        bytesize,
        parity,
        stopbits,
        xonxoff,
        rtscts,
        dsrdtr,
        **kwargs,
    ):
        """Read the data from the port."""
        print('serial_read:' + device)
        logged_error = False
        while True:
            try:
                loop = asyncio.get_event_loop()
                limit = asyncio.streams._DEFAULT_LIMIT
                reader = asyncio.StreamReader(limit=limit, loop=loop)
                protocol = Output(reader, loop=loop)
                # protocol = asyncio.StreamReaderProtocol(reader, loop=loop)
                transport, _ = await serial_asyncio.create_serial_connection(
                    loop=loop,
                    protocol_factory=lambda: protocol,
                    url=device,
                    baudrate=baudrate,
                    bytesize=bytesize,
                    parity=parity,
                    stopbits=stopbits,
                    xonxoff=xonxoff,
                    rtscts=rtscts,
                    dsrdtr=dsrdtr,
                    **kwargs)
                writer = asyncio.StreamWriter(transport, protocol, reader, loop)

                # reader, writer = await serial_asyncio.open_serial_connection(
                #     url=device,
                #     baudrate=baudrate,
                #     bytesize=bytesize,
                #     parity=parity,
                #     stopbits=stopbits,
                #     xonxoff=xonxoff,
                #     rtscts=rtscts,
                #     dsrdtr=dsrdtr,
                #     **kwargs,
                # )

            except SerialException as exc:
                print("SerialException")
                # if not logged_error:
                #     _LOGGER.exception(
                #         "Unable to connect to the serial device %s: %s. Will retry",
                #         device,
                #         exc,
                #     )
                #     logged_error = True
                await self._handle_error()
            else:
                print("Serial device %s connected", device)
                self._writer = writer
                while True:
                    try:
                        print("waiting")
                        if(reader.at_eof()):
                            break; 
                        line = await reader.readline()
                    except SerialException as exc:
                        _LOGGER.exception(
                            "Error while reading serial device %s: %s", device, exc
                        )
                        await self._handle_error()
                        break
                    else:
                        line = line.decode("utf-8").strip()

                        print("Received: %s", line)
                        # self._state = line
                        # self.async_write_ha_state()

    def send(self, code):
        """Send code."""
        # if self._writer is not None:
        #     self._writer.write(code)
        _LOG.info('Code %s sent', code)

    def get_port_state(self):
        """Get the current state of the port."""
        return 'on'

    @callback
    def stop_serial_read(self, event):
        """Close resources."""
        _LOG.error("stop_serial_read")
        if self._serial_loop_task:
            self._serial_loop_task.cancel()

    async def _handle_error(self):
        """Handle error for serial connection."""
        print("_handle_error")
        self._writer = None
        # self._state = None
        # self._attributes = None
        # self.async_write_ha_state()
        await asyncio.sleep(5)

class Output(asyncio.StreamReaderProtocol):
    _cancellable_reader = None

    def __init__(self, stream_reader, client_connected_cb=None, loop=None):
        super().__init__(stream_reader=stream_reader, loop=loop)
        self._cancellable_reader = stream_reader

    def connection_lost(self, exc):
        print('connection_lost')
        self._cancellable_reader.feed_eof()


def create_rcslink_gateway(config_entry, hass):
    """Create the rcslink gateway."""
    gateway = Gateway(config_entry, hass)
    return gateway
