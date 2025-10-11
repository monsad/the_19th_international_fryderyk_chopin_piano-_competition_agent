from opensearchpy import OpenSearch, helpers
from typing import List, Dict, Optional
from datetime import datetime, timedelta
from models import DataPoint, PredictionResponse, SourceType
import json

class OpenSearchClient:
    """OpenSearch client for storing and searching prediction data"""
    
    def __init__(
        self,
        host: str = "localhost",
        port: int = 9200,
        auth: tuple = ("admin", "admin"),
        use_ssl: bool = True,
        verify_certs: bool = False
    ):
        self.client = OpenSearch(
            hosts=[{"host": host, "port": port}],
            http_auth=auth,
            use_ssl=use_ssl,
            verify_certs=verify_certs,
            ssl_show_warn=False
        )
        
        self.indices = {
            "data_points": "war-prediction-data-points",
            "predictions": "war-prediction-predictions",
            "alerts": "war-prediction-alerts"
        }
        
        self._create_indices()
    
    def _create_indices(self):
        """Create indices with mappings if they don't exist"""
        
        # Data Points Index
        data_points_mapping = {
            "mappings": {
                "properties": {
                    "id": {"type": "keyword"},
                    "source": {"type": "keyword"},
                    "source_type": {"type": "keyword"},
                    "title": {"type": "text", "analyzer": "standard"},
                    "content": {"type": "text", "analyzer": "standard"},
                    "url": {"type": "keyword"},
                    "timestamp": {"type": "date"},
                    "relevance_score": {"type": "float"},
                    "sentiment": {"type": "float"},
                    "keywords": {"type": "keyword"},
                    "region": {"type": "keyword"},
                    "indexed_at": {"type": "date"}
                }
            }
        }
        
        # Predictions Index
        predictions_mapping = {
            "mappings": {
                "properties": {
                    "timestamp": {"type": "date"},
                    "global_risk_score": {"type": "float"},
                    "global_risk_level": {"type": "keyword"},
                    "regional_analyses": {"type": "nested"},
                    "confidence": {"type": "float"},
                    "reasoning": {"type": "text"},
                    "sources_analyzed": {"type": "integer"},
                    "key_events": {"type": "nested"}
                }
            }
        }
        
        # Alerts Index
        alerts_mapping = {
            "mappings": {
                "properties": {
                    "timestamp": {"type": "date"},
                    "alert_type": {"type": "keyword"},
                    "severity": {"type": "keyword"},
                    "region": {"type": "keyword"},
                    "message": {"type": "text"},
                    "risk_score": {"type": "float"},
                    "triggered_by": {"type": "keyword"}
                }
            }
        }
        
        for index_name, mapping in [
            (self.indices["data_points"], data_points_mapping),
            (self.indices["predictions"], predictions_mapping),
            (self.indices["alerts"], alerts_mapping)
        ]:
            if not self.client.indices.exists(index=index_name):
                self.client.indices.create(index=index_name, body=mapping)
                print(f"✅ Created index: {index_name}")
    
    async def index_data_point(self, data_point: DataPoint, region: str = "Global"):
        """Index a single data point"""
        doc = {
            "id": data_point.id,
            "source": data_point.source,
            "source_type": data_point.source_type.value,
            "title": data_point.title,
            "content": data_point.content,
            "url": data_point.url,
            "timestamp": data_point.timestamp.isoformat(),
            "relevance_score": data_point.relevance_score,
            "sentiment": data_point.sentiment,
            "keywords": data_point.keywords,
            "region": region,
            "indexed_at": datetime.now().isoformat()
        }
        
        self.client.index(
            index=self.indices["data_points"],
            id=data_point.id,
            body=doc
        )
    
    async def bulk_index_data_points(self, data_points: List[DataPoint]):
        """Bulk index data points"""
        actions = []
        for dp in data_points:
            actions.append({
                "_index": self.indices["data_points"],
                "_id": dp.id,
                "_source": {
                    "id": dp.id,
                    "source": dp.source,
                    "source_type": dp.source_type.value,
                    "title": dp.title,
                    "content": dp.content,
                    "url": dp.url,
                    "timestamp": dp.timestamp.isoformat(),
                    "relevance_score": dp.relevance_score,
                    "sentiment": dp.sentiment,
                    "keywords": dp.keywords,
                    "indexed_at": datetime.now().isoformat()
                }
            })
        
        if actions:
            helpers.bulk(self.client, actions)
            print(f"✅ Indexed {len(actions)} data points")
    
    async def index_prediction(self, prediction: PredictionResponse):
        """Index a prediction"""
        doc = {
            "timestamp": prediction.timestamp.isoformat(),
            "global_risk_score": prediction.global_risk_score,
            "global_risk_level": prediction.global_risk_level.value,
            "regional_analyses": [
                {
                    "region": ra.region,
                    "risk_score": ra.risk_score,
                    "risk_level": ra.risk_level.value,
                    "data_points_analyzed": ra.data_points_analyzed
                }
                for ra in prediction.regional_analyses
            ],
            "confidence": prediction.confidence,
            "reasoning": prediction.reasoning,
            "sources_analyzed": prediction.sources_analyzed,
            "key_events": [
                {
                    "title": ke.title,
                    "source": ke.source,
                    "relevance_score": ke.relevance_score
                }
                for ke in prediction.key_events[:10]
            ]
        }
        
        self.client.index(
            index=self.indices["predictions"],
            body=doc
        )
    
    async def search_data_points(
        self,
        query: str,
        source_type: Optional[SourceType] = None,
        start_date: Optional[datetime] = None,
        end_date: Optional[datetime] = None,
        min_relevance: float = 0.0,
        size: int = 100
    ) -> List[Dict]:
        """Search data points with filters"""
        
        must_clauses = [
            {"multi_match": {
                "query": query,
                "fields": ["title^2", "content", "keywords^3"]
            }}
        ]
        
        filter_clauses = []
        
        if source_type:
            filter_clauses.append({"term": {"source_type": source_type.value}})
        
        if start_date or end_date:
            range_query = {"timestamp": {}}
            if start_date:
                range_query["timestamp"]["gte"] = start_date.isoformat()
            if end_date:
                range_query["timestamp"]["lte"] = end_date.isoformat()
            filter_clauses.append({"range": range_query})
        
        if min_relevance > 0:
            filter_clauses.append({"range": {"relevance_score": {"gte": min_relevance}}})
        
        search_body = {
            "query": {
                "bool": {
                    "must": must_clauses,
                    "filter": filter_clauses
                }
            },
            "size": size,
            "sort": [
                {"relevance_score": {"order": "desc"}},
                {"timestamp": {"order": "desc"}}
            ]
        }
        
        response = self.client.search(
            index=self.indices["data_points"],
            body=search_body
        )
        
        return [hit["_source"] for hit in response["hits"]["hits"]]
    
    async def search_by_keywords(
        self,
        keywords: List[str],
        hours_back: int = 24,
        size: int = 50
    ) -> List[Dict]:
        """Search data points by keywords"""
        
        end_date = datetime.now()
        start_date = end_date - timedelta(hours=hours_back)
        
        search_body = {
            "query": {
                "bool": {
                    "must": [
                        {"terms": {"keywords": keywords}}
                    ],
                    "filter": [
                        {"range": {
                            "timestamp": {
                                "gte": start_date.isoformat(),
                                "lte": end_date.isoformat()
                            }
                        }}
                    ]
                }
            },
            "size": size,
            "sort": [{"timestamp": {"order": "desc"}}]
        }
        
        response = self.client.search(
            index=self.indices["data_points"],
            body=search_body
        )
        
        return [hit["_source"] for hit in response["hits"]["hits"]]
    
    async def get_predictions_history(
        self,
        start_date: Optional[datetime] = None,
        end_date: Optional[datetime] = None,
        min_risk_score: Optional[float] = None,
        size: int = 100
    ) -> List[Dict]:
        """Get prediction history with filters"""
        
        filter_clauses = []
        
        if start_date or end_date:
            range_query = {"timestamp": {}}
            if start_date:
                range_query["timestamp"]["gte"] = start_date.isoformat()
            if end_date:
                range_query["timestamp"]["lte"] = end_date.isoformat()
            filter_clauses.append({"range": range_query})
        
        if min_risk_score is not None:
            filter_clauses.append({"range": {"global_risk_score": {"gte": min_risk_score}}})
        
        search_body = {
            "query": {
                "bool": {
                    "filter": filter_clauses
                }
            } if filter_clauses else {"match_all": {}},
            "size": size,
            "sort": [{"timestamp": {"order": "desc"}}]
        }
        
        response = self.client.search(
            index=self.indices["predictions"],
            body=search_body
        )
        
        return [hit["_source"] for hit in response["hits"]["hits"]]
    
    async def aggregate_risk_by_region(self, days: int = 7) -> Dict:
        """Aggregate risk scores by region over time"""
        
        start_date = datetime.now() - timedelta(days=days)
        
        search_body = {
            "query": {
                "range": {
                    "timestamp": {"gte": start_date.isoformat()}
                }
            },
            "aggs": {
                "regions": {
                    "nested": {
                        "path": "regional_analyses"
                    },
                    "aggs": {
                        "by_region": {
                            "terms": {
                                "field": "regional_analyses.region",
                                "size": 50
                            },
                            "aggs": {
                                "avg_risk": {
                                    "avg": {
                                        "field": "regional_analyses.risk_score"
                                    }
                                },
                                "max_risk": {
                                    "max": {
                                        "field": "regional_analyses.risk_score"
                                    }
                                }
                            }
                        }
                    }
                }
            },
            "size": 0
        }
        
        response = self.client.search(
            index=self.indices["predictions"],
            body=search_body
        )
        
        buckets = response["aggregations"]["regions"]["by_region"]["buckets"]
        
        return {
            bucket["key"]: {
                "avg_risk": bucket["avg_risk"]["value"],
                "max_risk": bucket["max_risk"]["value"],
                "count": bucket["doc_count"]
            }
            for bucket in buckets
        }
    
    async def get_trending_keywords(self, hours: int = 24, size: int = 20) -> List[Dict]:
        """Get trending conflict keywords"""
        
        start_date = datetime.now() - timedelta(hours=hours)
        
        search_body = {
            "query": {
                "range": {
                    "timestamp": {"gte": start_date.isoformat()}
                }
            },
            "aggs": {
                "trending_keywords": {
                    "terms": {
                        "field": "keywords",
                        "size": size
                    }
                }
            },
            "size": 0
        }
        
        response = self.client.search(
            index=self.indices["data_points"],
            body=search_body
        )
        
        buckets = response["aggregations"]["trending_keywords"]["buckets"]
        
        return [
            {
                "keyword": bucket["key"],
                "count": bucket["doc_count"]
            }
            for bucket in buckets
        ]
    
    async def create_alert(
        self,
        alert_type: str,
        severity: str,
        region: str,
        message: str,
        risk_score: float,
        triggered_by: str
    ):
        """Create an alert"""
        doc = {
            "timestamp": datetime.now().isoformat(),
            "alert_type": alert_type,
            "severity": severity,
            "region": region,
            "message": message,
            "risk_score": risk_score,
            "triggered_by": triggered_by
        }
        
        self.client.index(
            index=self.indices["alerts"],
            body=doc
        )
    
    async def get_recent_alerts(self, hours: int = 24, size: int = 50) -> List[Dict]:
        """Get recent alerts"""
        
        start_date = datetime.now() - timedelta(hours=hours)
        
        search_body = {
            "query": {
                "range": {
                    "timestamp": {"gte": start_date.isoformat()}
                }
            },
            "size": size,
            "sort": [{"timestamp": {"order": "desc"}}]
        }
        
        response = self.client.search(
            index=self.indices["alerts"],
            body=search_body
        )
        
        return [hit["_source"] for hit in response["hits"]["hits"]]
    
    async def get_sentiment_analysis(self, hours: int = 24) -> Dict:
        """Analyze sentiment distribution"""
        
        start_date = datetime.now() - timedelta(hours=hours)
        
        search_body = {
            "query": {
                "range": {
                    "timestamp": {"gte": start_date.isoformat()}
                }
            },
            "aggs": {
                "sentiment_ranges": {
                    "range": {
                        "field": "sentiment",
                        "ranges": [
                            {"key": "very_negative", "to": -0.5},
                            {"key": "negative", "from": -0.5, "to": -0.1},
                            {"key": "neutral", "from": -0.1, "to": 0.1},
                            {"key": "positive", "from": 0.1, "to": 0.5},
                            {"key": "very_positive", "from": 0.5}
                        ]
                    }
                },
                "avg_sentiment": {
                    "avg": {"field": "sentiment"}
                }
            },
            "size": 0
        }
        
        response = self.client.search(
            index=self.indices["data_points"],
            body=search_body
        )
        
        return {
            "distribution": {
                bucket["key"]: bucket["doc_count"]
                for bucket in response["aggregations"]["sentiment_ranges"]["buckets"]
            },
            "average": response["aggregations"]["avg_sentiment"]["value"]
        }