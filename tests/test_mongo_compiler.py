"""Tests for MongoCompiler."""

from crossdb.core.ir import DocumentQueryArgs
from crossdb.backends.mongodb.compiler import MongoCompiler


def test_basic_mongo_pipeline_compilation():
    compiler = MongoCompiler()
    args = DocumentQueryArgs(
        collection_name="products",
        match_criteria={"category": "electronics", "price": {"$lt": 500}},
        pipeline_stages=[
            {"$lookup": {"from": "reviews", "localField": "_id", "foreignField": "product_id", "as": "reviews"}},
            {"$unwind": "$reviews"},
            {"$group": {"_id": "$_id", "avg_rating": {"$avg": "$reviews.rating"}}},
        ],
        projection={"_id": 1, "avg_rating": 1},
        limit=5,
    )
    pipeline = compiler.compile(args)
    assert len(pipeline) == 6
    assert pipeline[0] == {"$match": {"category": "electronics", "price": {"$lt": 500}}}
    assert pipeline[1]["$lookup"]["from"] == "reviews"
    assert pipeline[2] == {"$unwind": "$reviews"}
    assert "$group" in pipeline[3]
    assert pipeline[4] == {"$project": {"_id": 1, "avg_rating": 1}}
    assert pipeline[5] == {"$limit": 5}
