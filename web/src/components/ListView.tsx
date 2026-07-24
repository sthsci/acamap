import type { CampusSelection, PublicInstitution } from '../types';
import { InstitutionCard } from './InstitutionCard';

interface Props {
  institutions: PublicInstitution[];
  selectedId: string | null;
  selectedCampus: CampusSelection;
  onSelect: (id: string, campus: CampusSelection) => void;
}

export function ListView({ institutions, selectedId, selectedCampus, onSelect }: Props) {
  return (
    <div className="list-grid">
      {institutions.map((institution) => (
        <InstitutionCard
          key={institution.institution_id}
          institution={institution}
          selected={institution.institution_id === selectedId}
          selectedCampus={selectedCampus}
          onSelect={(campus) => onSelect(institution.institution_id, campus)}
        />
      ))}
    </div>
  );
}
