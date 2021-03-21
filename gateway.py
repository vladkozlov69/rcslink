"""The gateway to interact with a RCSLink port."""
import logging

from serial import SerialException
import serial_asyncio
import asyncio

from homeassistant.core import callback
from homeassistant.helpers.entity import Entity
from .const import DOMAIN, RCSLINK_SENSOR, CONF_SERIAL_PORT, RCSLINK_SENDER
from .exceptions import RCSLinkGatewayException

_LOGGER = logging.getLogger(__name__)
_LOGGER.setLevel(logging.DEBUG)

NO_RCSLINK_FOUND = "No RCSLink found"


class Gateway(Entity):
    """Gateway to interact with RCSLink."""
    _serial_loop_task = None
    _port_state = None
    _config_entry = None

    def __init__(self, config_entry, hass):
        """Initialize the RCSLink gateway."""
        self._hass = hass
        self._writer = None
        self._config_entry = config_entry
        hass.bus.async_listen("rcslink_send_command", 
                              self._handle_send_command)

    async def _handle_send_command(self, call):
        _LOGGER.info("Event received: %s", call.data)
        if 'command' in call.data:
            await self.send(call.data['command'])

    def get_sensor(self):
        """Returns the sensor instance from hass scope"""
        return self._hass.data[DOMAIN][RCSLINK_SENSOR]

    def get_port_state(self):
        """Returns the serial port state"""
        return self._port_state

    async def async_added_to_hass(self):
        """Handle when an entity is about to be added to Home Assistant."""
        _LOGGER.debug('Starting serial loop task')
        serial_port = self._config_entry.options[CONF_SERIAL_PORT]
        self._serial_loop_task = self._hass.loop.create_task(
            self.serial_read(
                serial_port,
                9600,
                serial_asyncio.serial.EIGHTBITS,
                serial_asyncio.serial.PARITY_NONE,
                serial_asyncio.serial.STOPBITS_ONE,
                False,
                False,
                False,
            )
        )

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
        logged_error = False
        while True:
            try:
                self._port_state = 'off'
                loop = asyncio.get_event_loop()
                limit = asyncio.streams._DEFAULT_LIMIT
                reader = asyncio.StreamReader(limit=limit, loop=loop)
                protocol = CancellableStreamReaderProtocol(reader, loop=loop)
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
                writer = asyncio.StreamWriter(transport,
                                              protocol,
                                              reader,
                                              loop)

            except SerialException as exc:
                if not logged_error:
                    _LOGGER.exception(
                        "Unable to connect to the serial device %s: %s." +
                        " Will retry",
                        device,
                        exc,
                    )
                    logged_error = True
                await self._handle_error()
            else:
                logged_error = False
                self._port_state = 'on'
                self._writer = writer
                _LOGGER.info('Port ready')
                _LOGGER.info(self._hass.data[DOMAIN])
                # Send registered codes to remote
                if RCSLINK_SENDER in self._hass.data[DOMAIN]:
                    sender = self._hass.data[DOMAIN][RCSLINK_SENDER]
                    _LOGGER.info(sender.ver())
                    await sender.refresh_codes('Writer exists')
                else:
                    _LOGGER.info('no sender in context')

                _LOGGER.info('Entering read loop')
                while True:
                    try:
                        if(reader.at_eof()):
                            self._writer = None
                            break
                        line = await reader.readline()
                    except SerialException as exc:
                        _LOGGER.exception(
                            "Error while reading serial device %s: %s",
                            device, exc
                        )
                        await self._handle_error()
                        break
                    else:
                        line = line.decode("utf-8").strip()

                        if (line.startswith('#:LEARNED ')):
                            code = line.replace('#:LEARNED ', '')
                            sender = self.get_sender()
                            if (sender is not None):
                                await sender.add_code(code)

                        sensor = self.get_sensor()
                        if (sensor is not None):
                            await sensor.notify(line)
                        else:
                            _LOGGER.error('No sensor in HASS context')

    async def send(self, code):
        """Send code."""
        if self._writer is not None:
            self._writer.write(str.encode(code + '\n'))
            await self._writer.drain()
            _LOGGER.info('>> %s', code)
        else:
            _LOGGER.exception('RCSLink Serial port unavailable')
            raise RCSLinkGatewayException('RCSLink Serial port unavailable')

    @callback
    def stop_serial_read(self, event):
        """Close resources."""
        _LOGGER.warn("Stopping serial read")
        if self._serial_loop_task:
            self._serial_loop_task.cancel()

    def get_sender(self):
        if RCSLINK_SENDER in self._hass.data[DOMAIN]:
            return self._hass.data[DOMAIN][RCSLINK_SENDER]
        return None

    async def _handle_error(self):
        """Handle error for serial connection."""
        self._writer = None
        self._port_state = 'off'
        await asyncio.sleep(5)


class CancellableStreamReaderProtocol(asyncio.StreamReaderProtocol):
    _cancellable_reader = None

    def __init__(self, stream_reader, client_connected_cb=None, loop=None):
        super().__init__(stream_reader=stream_reader, loop=loop)
        self._cancellable_reader = stream_reader

    def connection_lost(self, exc):
        _LOGGER.error('Connection lost, sending EOF to reader for restart')
        self._cancellable_reader.feed_eof()


def create_rcslink_gateway(config_entry, hass):
    """Create the rcslink gateway."""
    gateway = Gateway(config_entry, hass)
    return gateway
