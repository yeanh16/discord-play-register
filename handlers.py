from db import db
from utils import extract_remainder_after_fragments
from game import lookup_game_by_name_or_alias, find_games, games
from dotenv import load_dotenv
import os

load_dotenv()

CLIENT_ID = os.getenv('CLIENT_ID')

def create_mention(player):
    return '<@!%s>' % player.id


def get_any_ready_messages(game):
    if game.is_ready_to_play:
        return game.get_ready_messages()
    return []


def split_by_first_mention(message):
    msg = message.content
    if msg.startswith('<@'):
        idx = msg.index('>') + 1
        return msg[:idx], msg[idx:].strip()
    else:
        return '', msg


def is_bot_mention(mention):
    return mention[3 if mention.startswith('<@!') else 2:-1] == CLIENT_ID


class GameExtractionMixin:
    def get_all_responses(self, message):
        #self.game_name = extract_remainder_after_fragments(self.fragments, message.content)
        #self.game = lookup_game_by_name_or_alias(self.game_name)
        self.games = find_games(message.content);
        return self.get_all_responses_with_game(message, self.games)


class MessageHandler:
    def should_handle(self, message):
        raise NotImplementedError()

    def get_all_responses(self, message):
        raise NotImplementedError()


class ContentBasedHandler(MessageHandler):
    fragments = []

    def should_handle(self, message):
        return any(message.content.lower().startswith(f.lower()) for f in self.fragments)


class MentionMessageHandler(MessageHandler):
    keyword = None

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fragments = [self.keyword]

    def should_handle(self, message):
        mention, remainder = split_by_first_mention(message)
        return is_bot_mention(mention) and remainder.lower().startswith(self.keyword.lower())


class WouldPlayHandler(GameExtractionMixin, ContentBasedHandler):
    fragments = ["I'd play", "id play", "I'd paly", "id paly", "I’d play", "I’d paly", "I’dplay", "I’dpaly"]

    def get_all_responses_with_game(self, message, games):
        if games:
            message = "%s would play " % message.author.display_name
            for game in games:
                would_play = db.record_would_play(message.author, game)
                message += "%s (that's %s)\n" % (game, len(game.get_available_players())
            return [message]
        else:
            return []
        #if self.game_name:
        #    would_play = db.record_would_play(message.author, game)
        #    return ["%s would play %s (that's %s)" % (would_play.user, game, len(game.get_available_players()))] + get_any_ready_messages(game)
        #else:
        #    return []


class SameHandler(GameExtractionMixin, ContentBasedHandler):
    fragments = ['same to', 'same']

    def get_all_responses_with_game(self, message, games):
        would_play = []
        last_would_play = db.get_last_would_play(game)

        if not last_would_play:
            return ['Error! No fun here yet!']

        game = game or last_would_play.game 
        would_play = db.record_would_play(message.author.display_name, game) 

        return ["%s would also play %s (that's %s)" % (would_play.user, game, len(game.get_available_players()))] + get_any_ready_messages(game)


class StatusHandler(MentionMessageHandler):
    keyword = 'status'

    def get_all_responses(self, message):
        messages = ['Bot alive']
        ready_messages = []
        for game in games:
            players = game.get_available_players()
            if players:
                messages.append('%s has %s' % (game, len(players)))
                ready_messages += get_any_ready_messages(game)
        return ['\n'.join(messages + ready_messages)]


class ClearHandler(GameExtractionMixin, MentionMessageHandler):
    keyword = 'clear'

    def get_all_responses_with_game(self, message, games):
        if games:
            db.clear_game(games[0])
            return ['Cleared %s' % games[0]]
        else:
            return ['No game specified!']

class CancelHandler(MentionMessageHandler):
    keyword = 'cancel'

    def get_all_responses(self, message):
        db.cancel_would_plays(message.author)
        return ['Cancelled all play requests from %s' % (message.author.display_name)]


class PingHandler(GameExtractionMixin, MentionMessageHandler):
    keyword = 'ping'

    def get_all_responses_with_game(self, message, games):
        players = game.get_players_for_next_game()
        db.clear_game(game)
        return ['%s - ready to play %s.' % (','.join([create_mention(p) for p in players]), game)]


class AccidentalRoleMentionHandler(MessageHandler):
    def should_handle(self, message):
        return 'Play Register' in message.clean_content and '<@&' in message.content

    def get_all_responses(self, message):
        return ['It looks like you tried to @ me but might have accidentally selected the role instead']
