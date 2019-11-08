=====
Usage
=====

To use labstro in a project::

    from labstro.labstro import AutoprotocolToCelery
    from autoprotocol.protocol import Protocol

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


    AutoprotocolToCelery().to_celery(p.as_dict(), ["labstro.plugins.simulation"])

    ## output, a celery chain signature

    labstro.plugins.simulation.seal({'test pcr plate': {'new': '96-pcr', 'discard': True}}, {'op': 'seal', 'object': 'test pcr plate', 'type': 'foil', 'mode': 'thermal', 'mode_params': {'temperature': '165:celsius', 'duration': '1.5:second'}}) | spin({'test pcr plate': {'new': '96-pcr', 'discard': True}}, {'op': 'spin', 'object': 'test pcr plate', 'acceleration': '1000:g', 'duration': '1:minute'})

