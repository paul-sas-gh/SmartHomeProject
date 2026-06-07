import { GraphData, SparqlBinding } from '../types';

export function sparqlToGraphData(bindings: SparqlBinding[]): GraphData {
  const nodesMap = new Map<string, { id: string; label: string; type: string }>();
  const links: { source: string; target: string; label: string }[] = [];

  bindings.forEach((row) => {
    const subject = row.s?.value;
    const predicate = row.p?.value;
    const object = row.o?.value;

    if (!subject || !predicate || !object) return;

    const getLabel = (uri: string) => {
      const parts = uri.split(/[/#]/);
      return parts[parts.length - 1] || uri;
    };

    const getType = (uri: string) => {
      if (uri.includes('Room')) return 'Room';
      if (uri.includes('Sensor')) return 'Sensor';
      if (uri.includes('Actuator')) return 'Actuator';
      if (uri.includes('Action')) return 'Action';
      if (uri.includes('SmartHub')) return 'SmartHub';
      if (uri.includes('RoutineStep')) return 'RoutineStep';
      return 'Entity';
    };

    if (!nodesMap.has(subject)) {
      nodesMap.set(subject, {
        id: subject,
        label: getLabel(subject),
        type: getType(subject),
      });
    }

    if (!nodesMap.has(object)) {
      nodesMap.set(object, {
        id: object,
        label: getLabel(object),
        type: getType(object),
      });
    }

    links.push({
      source: subject,
      target: object,
      label: getLabel(predicate),
    });
  });

  return {
    nodes: Array.from(nodesMap.values()),
    links,
  };
}

export const nodeColors: Record<string, string> = {
  Room: '#3b82f6',
  Sensor: '#22c55e',
  Actuator: '#f97316',
  Action: '#ef4444',
  SmartHub: '#a855f7',
  RoutineStep: '#06b6d4',
  Entity: '#64748b',
};
