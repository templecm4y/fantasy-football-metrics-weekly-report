__author__ = "Wren J. R. (uberfastman)"
__email__ = "wrenjr@yahoo.com"

import datetime
import json
import logging
import os
from configparser import ConfigParser

from slack import WebClient
from slack.errors import SlackApiError

logger = logging.getLogger(__name__)


class SlackMessenger(object):
    def __init__(self, config):

        self.project_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

        self.config = config  # type: ConfigParser

        auth_token = os.path.join(self.project_dir, self.config.get("Slack", "slack_auth_token"))

        with open(auth_token, "r") as token_file:
            # more information at https://api.slack.com/web#authentication
            slack_api_access_token = json.load(token_file).get("access_token")
            # self.sc = SlackClient(slack_api_access_token)
            self.sc = WebClient(token=slack_api_access_token)

    def api_test(self):
        try:
            return self.sc.api_test()
        except SlackApiError as e:
            logger.error("Slack client error: %s", e)

    def list_channels(self):
        """Required Slack app scopes: channels:read, groups:read, mpim:read, im:read
        """
        try:
            return self.sc.conversations_list()
        except SlackApiError as e:
            logger.error("Slack client error: %s", e)

    def get_channel_id(self, channel_name):
        for channel in self.list_channels().get("channels"):
            if channel.get("name") == channel_name:
                return channel.get("id")

    def test_post_to_slack(self, message):
        try:
            logger.info(self.sc.conversations_info(channel=self.get_channel_id("apitest")))

            self.sc.chat_postMessage(
                channel=self.get_channel_id("apitest"),
                text="<!here|here>:\n" + message,
                username="ff-report",
                # uncomment the icon_emoji parameter if you wish to choose an icon emoji to be your app icon, otherwise
                # it will default to whatever icon you have set for the app
                # icon_emoji=":football:"
            )
        except SlackApiError as e:
            logger.error("Slack client error: %s", e)

    def test_file_upload_to_slack(self, upload_file):
        try:
            logger.info(self.sc.conversations_info(channel=self.get_channel_id("apitest")))

            with open(upload_file, "rb") as uf:
                file_to_upload = uf.read()

                response = self.sc.files_upload(
                    channels=self.get_channel_id("apitest"),
                    username="ff-report",
                    icon_emoji=":football:",
                    filename=upload_file,
                    filetype="pdf",
                    file=file_to_upload
                )
            return response
        except SlackApiError as e:
            logger.error("Slack client error: %s", e)

    def post_to_selected_slack_channel(self, message):
        try:
            return self.sc.chat_postMessage(
                channel=self.get_channel_id(self.config.get("Slack", "slack_channel")),
                text="<!here|here>\n" + message,
                username="ff-report",
                # icon_emoji=":football:"
            )
        except SlackApiError as e:
            logger.error("Slack client error: %s", e)

    def upload_file_to_selected_slack_channel(self, upload_file):

        try:
            report_file_info = upload_file.split(os.sep)
            file_name = report_file_info[-1]
            file_type = file_name.split(".")[-1]
            league_name = report_file_info[-2]
            message = "\nFantasy Football Report for %s\nGenerated %s\n" % (league_name,
                                                                            "{:%Y-%b-%d %H:%M:%S}".format(
                                                                                datetime.datetime.now()))

            upload_file = os.path.join(self.project_dir, upload_file)
            with open(upload_file, "rb") as uf:

                if self.config.getboolean("Slack", "notify_channel"):
                    # post message with no additional content to trigger @here
                    self.post_to_selected_slack_channel("")

                file_to_upload = uf.read()
                response = self.sc.files_upload(
                    channels=self.get_channel_id(self.config.get("Slack", "slack_channel")),
                    filename=file_name,
                    filetype=file_type,
                    file=file_to_upload,
                    title=file_name,
                    initial_comment=message
                )
            return response
        except SlackApiError as e:
            logger.error("Slack client error: %s", e)


if __name__ == '__main__':
    local_config = ConfigParser()
    local_config.read(os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "config.ini"))
    repost_file = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
                               local_config.get("Slack", "repost_file"))

    post_to_slack = SlackMessenger(local_config)

    # print(post_to_slack.api_test())
    # print(post_to_slack.list_channels().get("channels"))
    # print(post_to_slack.test_post_to_slack("test"))
    # print(post_to_slack.test_file_upload_to_slack(repost_file))
    # print(post_to_slack.post_to_selected_slack_channel("test"))
    print(post_to_slack.upload_file_to_selected_slack_channel(repost_file))
