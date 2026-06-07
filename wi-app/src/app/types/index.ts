export interface GraphNode {
  id: string;
  label: string;
  type: string;
}

export interface GraphLink {
  source: string;
  target: string;
  label: string;
}

export interface GraphData {
  nodes: GraphNode[];
  links: GraphLink[];
}

export interface Entity {
  label: string;
  uri_name: string;
  entity_type: string;
  confidence: number;
  source_text?: string;
}

export interface Relation {
  subject: string;
  predicate: string;
  object: string;
  confidence: number;
  source_text?: string;
}

export interface ProcessResponse {
  source: string;
  entity_count: number;
  relation_count: number;
  triple_count: number;
  graphdb_uploaded: boolean;
  entities: Entity[];
  relations: Relation[];
  ttl_path: string;
}

export interface SparqlBinding {
  [key: string]: {
    type: string;
    value: string;
  };
}

export interface SparqlResponse {
  repository: string;
  query: string;
  result_count: number;
  results: SparqlBinding[];
}

export interface PredefinedQueryResponse {
  query_id: number;
  query_name: string;
  description: string;
  result_count: number;
  results: any[];
}
