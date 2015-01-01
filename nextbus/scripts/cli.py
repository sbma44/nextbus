# Skeleton of a CLI

import click

import nextbus


@click.command('nextbus')
@click.argument('count', type=int, metavar='N')
def cli(count):
    """Echo a value `N` number of times"""
    for i in range(count):
        click.echo(nextbus.has_legs)
