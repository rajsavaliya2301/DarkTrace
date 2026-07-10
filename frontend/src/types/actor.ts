export interface Actor {
  id: string;
  pseudonyms: string[];
  risk_score: number;
  first_seen: string;
  last_seen: string;
  total_posts: number;
  active_platforms: string[];
  linked_entities: {
    btc_addresses: number;
    emails: number;
    pgp_keys: number;
  };
  top_categories: string[];
  source_url: string;
  source_title: string;
  urls: string[];
  content_ids: string[];
  recent_activity: ActorRecentContent[];
}

export interface ActorDetail {
  id: string;
  pseudonyms: ActorPseudonym[];
  risk_score: number;
  risk_factors: string[];
  first_seen: string;
  last_seen: string;
  total_posts: number;
  active_platforms: string[];
  linked_entities: {
    btc_addresses: ActorBTCAddress[];
    emails: string[];
    pgp_keys: string[];
  };
  activity_timeline: ActorActivity[];
  recent_activity: ActorRecentContent[];
  network_graph: NetworkGraph;
}

export interface ActorPseudonym {
  name: string;
  platforms: string[];
  first_seen: string;
  last_seen: string;
}

export interface ActorBTCAddress {
  address: string;
  first_seen: string;
  total_received_btc: number;
}

export interface ActorActivity {
  date: string;
  posts: number;
  categories: string[];
}

export interface ActorRecentContent {
  content_id: string;
  url: string;
  title: string;
  category: string;
  crawled_at: string;
}

export interface NetworkGraph {
  nodes: GraphNode[];
  edges: GraphEdge[];
}

export interface GraphNode {
  id: string;
  label: string;
  type: 'actor' | 'site' | 'address' | 'email';
  risk_score?: number;
}

export interface GraphEdge {
  source: string;
  target: string;
  label: string;
  count?: number;
}
