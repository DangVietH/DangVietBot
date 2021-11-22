from discord.ext.commands.errors import CheckFailure


class NotConnectedToVoice(CheckFailure):
    pass


class PlayerNotConnected(CheckFailure):
    pass


class MustBeSameChannel(CheckFailure):
    pass