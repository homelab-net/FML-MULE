#!/usr/bin/env python3
"""Send one position event to the CoT listener and exit.

The transport is PyTAK, which is the client this program prefers. The event
is synthetic. This does not exercise enrollment or a real TAK application.
"""

from __future__ import annotations

import asyncio
import os
import xml.etree.ElementTree as ET
from configparser import ConfigParser

import pytak

UID = "fml-topology-pli"


class OnePosition(pytak.QueueWorker):  # type: ignore[misc]
    """Queue a single PLI, then stop the process."""

    async def run(self) -> None:
        """Queue one event and leave the process."""
        event = ET.Element("event")
        event.set("version", "2.0")
        event.set("type", "a-f-G-U-C")
        event.set("uid", UID)
        event.set("how", "m-g")
        event.set("time", pytak.cot_time())
        event.set("start", pytak.cot_time())
        event.set("stale", pytak.cot_time(120))
        point = ET.SubElement(event, "point")
        point.set("lat", "39.7392")
        point.set("lon", "-104.9903")
        point.set("hae", "1608")
        point.set("ce", "10")
        point.set("le", "10")
        await self.put_queue(ET.tostring(event))
        await asyncio.sleep(1)
        os._exit(0)


async def main() -> None:
    parser = ConfigParser()
    parser["sender"] = {"COT_URL": "tcp://eud-handler:8088"}
    config = parser["sender"]
    tool = pytak.CLITool(config)
    await tool.setup()
    tool.add_tasks({OnePosition(tool.tx_queue, config)})
    await tool.run()


if __name__ == "__main__":
    asyncio.run(main())
