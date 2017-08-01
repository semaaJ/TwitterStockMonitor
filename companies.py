class Companies(object):
    def __init__(self, tweet='', handle=None):
        if tweet != '':
            self.tweet = tweet.decode('utf8')
            self.original_tweet = self.tweet  # Keeping a copy for later use, as self.tweet is edited
        else:
            self.tweet = tweet
        self.handle = handle

    def check_for_companies(self):
        """Checks list of companies with Trump's tweet
           seeing if any companies are listed in his tweet.
           Inputs matches into monitor.json"""

        matches = []
        punc = ("!", ",", ".", ":", ";", "@", "?", "(", ")")

        self.tweet = ''.join([letter for letter in self.tweet if letter not in punc]).lower()

        with open(COMPANIES) as f:
            companies = [line.strip() for line in f]

        for word in self.tweet.split():
            # Binary search for word
            if utils.find(companies, word):
                matches.append(word)

        company_dict = utils.open_json(MONITOR)
        comp_d = {}

        # Information that is needed by get_initial/current
        for company in matches:
            comp_d[company] = {}
            comp_d[company]["Date-mentioned"] = "{:%d-%m-%Y %H:%M:%S}".format(datetime.datetime.now())
            comp_d[company]["Mentioned by"] = self.handle
            comp_d[company]["Tweet"] = self.original_tweet
            comp_d[company]["Days-left"] = 7
            comp_d[company]["Symbol"] = "unknown"
            comp_d[company]["Initial-share-price"] = 1
            comp_d[company]["Current-share-price"] = 1
            comp_d[company]["Share-price-list"] = []

        company_dict.update(comp_d)
        utils.write_to_json(MONITOR, company_dict)

        return matches

    @staticmethod
    def get_initial_company_info():
        """Gets the initial information for each company"""

        company_dict = utils.open_json(MONITOR)

        for company in company_dict:
            # Gets symbol for company
            if company_dict[company]["Symbol"] == "unknown":
                try:
                    with urllib.request.urlopen(
                          f'https://finance.yahoo.com/_finance_doubledown/'
                          f'api/resource/searchassist;searchTerm={company}') as response:

                        html = response.read().decode()
                        d = json.loads(html)

                        company_dict[company]["Symbol"] = d['items'][0]['symbol']

                except urllib.error.HTTPError as error:
                    utils.write_to_log(f'Error opening URL: {error}')

            # Gets initial share price
            if company_dict[company]["Initial-share-price"] == 1:
                yahoo = Share(company_dict[company]["Symbol"])
                share = yahoo.get_price()
                company_dict[company]["Initial-share-price"] = float(share)
                company_dict[company]["Current-share-price"] = float(share)

        utils.write_to_json(MONITOR, company_dict)

    @staticmethod
    def get_current_shares():
        """Gets current shares, compares it to initial, finds difference.
           Returns for output to handle"""

        company_dict = utils.open_json(MONITOR)

        for company in company_dict:
            try:
                yahoo = Share(company_dict[company]["Symbol"])
                yahoo.refresh()
                share = yahoo.get_price()

                company_dict[company]["Current-share-price"] = float(share)
                company_dict[company]["Share-price-list"].append(float(share))

            except ValueError:
                # yahoo.get_price() will return None if an error occurs
                print("Could not add to the Current share/Share price list")

        utils.write_to_json(MONITOR, company_dict)

    @staticmethod
    def difference_in_shares():
        """Finds the difference in shares.
           Creates a dict to be used by Output"""

        company_dict = utils.open_json(MONITOR)

        share_difference_dict = {}

        for company in company_dict:
            share_change = 1.0 - (company_dict[company]["Initial-share-price"] /
                                  company_dict[company]["Current-share-price"])

            maximum = 1 - (company_dict[company]["Initial-share-price"] /
                           max(company_dict[company]["Share-price-list"]))

            share_difference_dict[company] = {}
            share_difference_dict[company]["Change"] = share_change
            share_difference_dict[company]["Max"] = max(company_dict[company]["Share-price-list"])
            share_difference_dict[company]["Max-change"] = maximum
            share_difference_dict[company]["Initial"] = company_dict[company]["Initial-share-price"]
            share_difference_dict[company]["Current"] = company_dict[company]["Current-share-price"]

        return share_difference_dict

    @staticmethod
    def minus_days():
        """Takes away a day from the "Days-Left",
           removes from monitor.json if == 0"""

        company_dict = utils.open_json(MONITOR)
        remove = []

        for company in company_dict:
            if company_dict[company]["Days-left"] > 0:
                company_dict[company]["Days-left"] -= 1

            elif company_dict[company]["Days-left"] == 0:
                remove.append(company)

        for company in remove:
            # Do I want to keep a record of all the companies that have been mentioned and their prices???
            # Goes here
            del company_dict[company]

        utils.write_to_json(MONITOR, company_dict)
