#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""Tests for `labstro` package."""


import unittest
from click.testing import CliRunner

from labstro.labstro import AutoprotocolToCelery
from labstro import cli

import json
from autoprotocol.protocol import Protocol
from labstro.plugins.simulation import seal, spin

from celery import chain
import importlib


class TestAutoprotocolToCelery(unittest.TestCase):
    """Tests for `labstro` package."""

    def setUp(self):
        """Set up test fixtures, if any."""
        # instantiate a protocol object
        p = Protocol()

        # generate a ref
        # specify where it comes from and how it should be handled when the Protocol is done
        plate = p.ref("test pcr plate", id=None, cont_type="96-pcr", discard=True)

        # generate seal and spin instructions that act on the ref
        # some parameters are explicitly specified and others are left to vendor defaults
        p.seal(
            ref=plate,
            type="foil",
            mode="thermal",
            temperature="165:celsius",
            duration="1.5:seconds"
        )
        p.spin(
            ref=plate,
            acceleration="1000:g",
            duration="1:minute"
        )

        # serialize the protocol as Autoprotocol JSON
        self.protocol_json = json.dumps(p.as_dict(), indent=2)
        self.protocol_dict = p.as_dict()

        self.operations = [i["op"] for i in self.protocol_dict["instructions"]]

        self.plugins = ["labstro.plugins.simulation"]

        self.plugin_module = importlib.import_module(self.plugins[0])

        self.plugin_dict = {"seal":["labstro.plugins.simulation.seal"],
                          "spin":["labstro.plugins.simulation.spin"]}

        self.plugin_sigs = {k:getattr(self.plugin_module, k) for k,v in self.plugin_dict.items()}

    def tearDown(self):
        """Tear down test fixtures, if any."""

    def test_000_something(self):
        """Test something."""

    def test_command_line_interface(self):
        """Test the CLI."""
        runner = CliRunner()
        result = runner.invoke(cli.main)
        assert result.exit_code == 0
        assert 'labstro.cli.main' in result.output
        help_result = runner.invoke(cli.main, ['--help'])
        assert help_result.exit_code == 0
        assert '--help  Show this message and exit.' in help_result.output

    def test_route_plugins(self):
        result = AutoprotocolToCelery.route_plugins(self.operations,
                                       self.plugins)

        assert result == self.plugin_dict


    def test_import_task(self):
         result = AutoprotocolToCelery.import_task("seal", self.plugin_dict)


         assert result == getattr(self.plugin_module, "seal")
