import { Filter } from 'lucide-react';

interface FilterPanelProps {
  selectedType: string;
  onTypeChange: (type: string) => void;
}

const ENTITY_TYPES = [
  { value: 'all', label: 'All Entities' },
  { value: 'Room', label: 'Rooms', color: 'bg-blue-500' },
  { value: 'Sensor', label: 'Sensors', color: 'bg-green-500' },
  { value: 'Actuator', label: 'Actuators', color: 'bg-orange-500' },
  { value: 'Action', label: 'Actions', color: 'bg-red-500' },
  { value: 'SmartHub', label: 'Smart Hubs', color: 'bg-purple-500' },
  { value: 'RoutineStep', label: 'Routine Steps', color: 'bg-cyan-500' },
];

export function FilterPanel({ selectedType, onTypeChange }: FilterPanelProps) {
  return (
    <div className="bg-white rounded-lg border border-slate-200 p-4">
      <div className="flex items-center gap-2 mb-3">
        <Filter className="w-4 h-4 text-slate-600" />
        <h3 className="font-semibold text-slate-800">Filters</h3>
      </div>

      <div className="space-y-2">
        <label className="block text-sm font-medium text-slate-700 mb-2">Entity Type</label>
        <div className="grid grid-cols-2 gap-2">
          {ENTITY_TYPES.map((type) => (
            <button
              key={type.value}
              onClick={() => onTypeChange(type.value)}
              className={`flex items-center gap-2 px-3 py-2 rounded-md text-sm transition-all ${
                selectedType === type.value
                  ? 'bg-blue-50 border-2 border-blue-500 text-blue-700 font-medium'
                  : 'bg-slate-50 border border-slate-200 text-slate-700 hover:bg-slate-100'
              }`}
            >
              {type.color && <span className={`w-3 h-3 rounded-full ${type.color}`} />}
              <span>{type.label}</span>
            </button>
          ))}
        </div>
      </div>

      <div className="mt-4 pt-4 border-t border-slate-200">
        <div className="text-xs text-slate-600">
          <div className="font-semibold mb-2">Legend</div>
          <div className="space-y-1">
            {ENTITY_TYPES.slice(1).map((type) => (
              <div key={type.value} className="flex items-center gap-2">
                <span className={`w-2 h-2 rounded-full ${type.color}`} />
                <span>{type.label}</span>
              </div>
            ))}
          </div>
        </div>
      </div>
    </div>
  );
}
