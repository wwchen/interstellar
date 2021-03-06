from PlayStoreReview.Database.Result import Result
from PlayStoreReview.Review import Review


class ReviewProcessor:
    def __init__(self, database):
        # todo sanity assert database object
        self._db = database
        self._reviews = []
        self._avg_stars = 0
        self._notable_reviews = None
        self._count_new = 0

    def add(self, review):
        assert isinstance(review, Review)
        self._reviews.append(review)

    def process(self):
        if not len(self._reviews):
            return
        for review in self._reviews:
            review_fetched = self._db.get_review(review.id)
            if review == review_fetched:
                pass
            else:
                result = self._db.insert(review)
                if result == Result.inserted:
                    self._count_new += 1

        stars = 0
        notable_reviews = []
        for review in self._reviews:
            assert isinstance(review.review_rating, int)
            stars += review.review_rating
            if self._is_review_notable(review):
                notable_reviews.append(review)
        self._avg_stars = float(stars) / len(self._reviews)
        self._notable_reviews = notable_reviews

    def _is_review_notable(self, review):
        if review.review_lang == "en":
            if review.review_title and review.review_text:
                return True
        return False

    def __str__(self):
        if not self._reviews:
            return "No reviews accumulated"
        self.process()
        count = 4
        self._notable_reviews.sort(key=lambda r: r.review_update_epoch)
        for review in self._notable_reviews:
            if count > 0:
                print review
            else:
                break
            count -= 1
        return "Overall stats: %0.2f stars\nNew reviews: %d" % (self._avg_stars, self._count_new)


