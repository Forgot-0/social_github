import { useState } from "react";
import { Plus, Pencil, Trash2, X } from "lucide-react";
import { api } from "../lib/api";
import { toast } from "sonner";
import { StyledSelect } from './StyledSelect';

interface Position {
  id: string;
  project_id: number;
  title: string;
  description: string;
  responsibilities: string;
  required_skills: string[];
  is_open: boolean;
  location_type: "remote" | "onsite" | "hybrid";
  expected_load: "low" | "medium" | "high";
}

interface PositionManagerProps {
  projectId: number;
  positions: Position[];
  onUpdate: () => void;
  isOwner: boolean;
}

export function PositionManager({ projectId, positions, onUpdate, isOwner }: PositionManagerProps) {
  const [showForm, setShowForm] = useState(false);
  const [editingId, setEditingId] = useState<string | null>(null);
  const [formData, setFormData] = useState({
    title: "",
    description: "",
    responsibilities: "",
    required_skills: [] as string[],
    is_open: true,
    location_type: "remote" as "remote" | "onsite" | "hybrid",
    expected_load: "medium" as "low" | "medium" | "high",
  });
  const [skillInput, setSkillInput] = useState("");

  const resetForm = () => {
    setFormData({
      title: "",
      description: "",
      responsibilities: "",
      required_skills: [],
      is_open: true,
      location_type: "remote",
      expected_load: "medium",
    });
    setSkillInput("");
    setEditingId(null);
    setShowForm(false);
  };

  const handleEdit = (position: Position) => {
    setFormData({
      title: position.title,
      description: position.description,
      responsibilities: position.responsibilities,
      required_skills: position.required_skills,
      is_open: position.is_open,
      location_type: position.location_type,
      expected_load: position.expected_load,
    });
    setEditingId(position.id);
    setShowForm(true);
  };

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();

    if (!formData.title || !formData.description) {
      toast.error("Заполните обязательные поля");
      return;
    }

    try {
      if (editingId) {
        await api.updatePosition(editingId, formData);
        toast.success("Позиция обновлена");
      } else {
        await api.createPosition(projectId, formData);
        toast.success("Позиция создана");
      }
      onUpdate();
      resetForm();
    } catch (error: any) {
      console.error("Failed to save position:", error);
      toast.error(error?.error?.message || "Ошибка при сохранении позиции");
    }
  };

  const handleDelete = async (positionId: string) => {
    if (!confirm("Вы уверены, что хотите удалить эту позицию?")) {
      return;
    }

    try {
      await api.deletePosition(positionId);
      toast.success("Позиция удалена");
      onUpdate();
    } catch (error: any) {
      console.error("Failed to delete position:", error);
      toast.error(error?.error?.message || "Ошибка при удалении позиции");
    }
  };

  const addSkill = () => {
    const skill = skillInput.trim();
    if (skill && !formData.required_skills.includes(skill)) {
      setFormData({ ...formData, required_skills: [...formData.required_skills, skill] });
      setSkillInput("");
    }
  };

  const removeSkill = (skillToRemove: string) => {
    setFormData({
      ...formData,
      required_skills: formData.required_skills.filter((skill) => skill !== skillToRemove),
    });
  };

  if (!isOwner) {
    return (
      <div className="space-y-4">
        {positions.map((position) => (
          <div key={position.id} className="p-6 border border-border rounded-lg">
            <h3 className="text-xl font-semibold mb-2">{position.title}</h3>
            <p className="text-muted-foreground mb-3">{position.description}</p>
            <div className="flex flex-wrap gap-2 mb-3">
              {position.required_skills.map((skill) => (
                <span key={skill} className="px-3 py-1 bg-secondary text-secondary-foreground text-sm rounded-full">
                  {skill}
                </span>
              ))}
            </div>
            <div className="flex gap-4 text-sm text-muted-foreground">
              <span className="capitalize">
                {position.location_type === "remote" ? "Удаленно" : position.location_type === "hybrid" ? "Гибрид" : "Офис"}
              </span>
              <span>•</span>
              <span className="capitalize">
                {position.expected_load === "low" ? "Низкая нагрузка" : position.expected_load === "medium" ? "Средняя нагрузка" : "Высокая нагрузка"}
              </span>
            </div>
          </div>
        ))}
      </div>
    );
  }

  return (
    <div>
      {!showForm && (
        <button
          onClick={() => setShowForm(true)}
          className="flex items-center space-x-2 px-4 py-2 bg-primary text-white rounded-lg hover:bg-accent transition-colors mb-6"
        >
          <Plus className="w-5 h-5" />
          <span>Добавить позицию</span>
        </button>
      )}

      {showForm && (
        <form onSubmit={handleSubmit} className="bg-secondary/50 rounded-lg p-6 mb-6 space-y-4">
          <div className="flex items-center justify-between mb-4">
            <h3 className="text-xl font-semibold">
              {editingId ? "Редактировать позицию" : "Новая позиция"}
            </h3>
            <button type="button" onClick={resetForm} className="text-muted-foreground hover:text-foreground">
              <X className="w-5 h-5" />
            </button>
          </div>

          <div>
            <label className="block text-sm font-medium mb-2">
              Название <span className="text-red-500">*</span>
            </label>
            <input
              type="text"
              value={formData.title}
              onChange={(e) => setFormData({ ...formData, title: e.target.value })}
              placeholder="Frontend разработчик"
              className="app-select"
              required
            />
          </div>

          <div>
            <label className="block text-sm font-medium mb-2">
              Описание <span className="text-red-500">*</span>
            </label>
            <textarea
              value={formData.description}
              onChange={(e) => setFormData({ ...formData, description: e.target.value })}
              placeholder="Описание позиции"
              rows={3}
              className="app-textarea min-h-[96px]"
              required
            />
          </div>

          <div>
            <label className="block text-sm font-medium mb-2">Обязанности</label>
            <textarea
              value={formData.responsibilities}
              onChange={(e) => setFormData({ ...formData, responsibilities: e.target.value })}
              placeholder="Основные обязанности"
              rows={3}
              className="app-textarea min-h-[96px]"
            />
          </div>

          <div>
            <label className="block text-sm font-medium mb-2">Требуемые навыки</label>
            <div className="flex space-x-2 mb-2">
              <input
                type="text"
                value={skillInput}
                onChange={(e) => setSkillInput(e.target.value)}
                onKeyDown={(e) => {
                  if (e.key === "Enter") {
                    e.preventDefault();
                    addSkill();
                  }
                }}
                placeholder="React, TypeScript..."
                className="flex-1 px-4 py-2 bg-white border border-border rounded-lg focus:outline-none focus:ring-2 focus:ring-primary"
              />
              <button
                type="button"
                onClick={addSkill}
                className="px-4 py-2 bg-primary text-white rounded-lg hover:bg-accent transition-colors"
              >
                <Plus className="w-5 h-5" />
              </button>
            </div>
            <div className="flex flex-wrap gap-2">
              {formData.required_skills.map((skill) => (
                <span
                  key={skill}
                  className="inline-flex items-center space-x-2 px-3 py-1 bg-white border border-border rounded-full"
                >
                  <span>{skill}</span>
                  <button type="button" onClick={() => removeSkill(skill)} className="hover:text-red-500">
                    <X className="w-4 h-4" />
                  </button>
                </span>
              ))}
            </div>
          </div>

          <div className="grid grid-cols-2 gap-4">
            <div>
              <label className="block text-sm font-medium mb-2">Формат работы</label>
              <StyledSelect
                value={formData.location_type}
                onChange={(value) => setFormData({ ...formData, location_type: value as any })}
                options={[
                  { value: 'remote', label: 'Удаленно' },
                  { value: 'onsite', label: 'Офис' },
                  { value: 'hybrid', label: 'Гибрид' },
                ]}
              />
            </div>

            <div>
              <label className="block text-sm font-medium mb-2">Нагрузка</label>
              <StyledSelect
                value={formData.expected_load}
                onChange={(value) => setFormData({ ...formData, expected_load: value as any })}
                options={[
                  { value: 'low', label: 'Низкая' },
                  { value: 'medium', label: 'Средняя' },
                  { value: 'high', label: 'Высокая' },
                ]}
              />
            </div>
          </div>

          <div>
            <label className="flex items-center space-x-2">
              <input
                type="checkbox"
                checked={formData.is_open}
                onChange={(e) => setFormData({ ...formData, is_open: e.target.checked })}
                className="w-4 h-4 text-primary focus:ring-primary"
              />
              <span className="text-sm">Позиция открыта</span>
            </label>
          </div>

          <div className="flex space-x-4">
            <button type="submit" className="flex-1 py-2 bg-primary text-white rounded-lg hover:bg-accent transition-colors">
              {editingId ? "Сохранить" : "Создать"}
            </button>
            <button type="button" onClick={resetForm} className="px-6 py-2 bg-white border border-border rounded-lg hover:bg-secondary transition-colors">
              Отмена
            </button>
          </div>
        </form>
      )}

      <div className="space-y-4">
        {positions.map((position) => (
          <div key={position.id} className="p-6 border border-border rounded-lg">
            <div className="flex items-start justify-between mb-2">
              <h3 className="text-xl font-semibold">{position.title}</h3>
              <div className="flex space-x-2">
                <button
                  onClick={() => handleEdit(position)}
                  className="p-2 text-muted-foreground hover:text-primary transition-colors"
                >
                  <Pencil className="w-4 h-4" />
                </button>
                <button
                  onClick={() => handleDelete(position.id)}
                  className="p-2 text-muted-foreground hover:text-red-500 transition-colors"
                >
                  <Trash2 className="w-4 h-4" />
                </button>
              </div>
            </div>
            <p className="text-muted-foreground mb-3">{position.description}</p>
            <div className="flex flex-wrap gap-2 mb-3">
              {position.required_skills.map((skill) => (
                <span key={skill} className="px-3 py-1 bg-secondary text-secondary-foreground text-sm rounded-full">
                  {skill}
                </span>
              ))}
            </div>
            <div className="flex gap-4 text-sm text-muted-foreground">
              <span className="capitalize">
                {position.location_type === "remote" ? "Удаленно" : position.location_type === "hybrid" ? "Гибрид" : "Офис"}
              </span>
              <span>•</span>
              <span className="capitalize">
                {position.expected_load === "low" ? "Низкая нагрузка" : position.expected_load === "medium" ? "Средняя нагрузка" : "Высокая нагрузка"}
              </span>
              <span>•</span>
              <span className={position.is_open ? "text-green-600" : "text-red-600"}>
                {position.is_open ? "Открыта" : "Закрыта"}
              </span>
            </div>
          </div>
        ))}
      </div>
    </div>
  );
}