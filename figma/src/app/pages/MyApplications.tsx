import { useState, useEffect } from "react";
import { Link } from "react-router-dom";
import { Briefcase, Calendar, Clock, CheckCircle, XCircle } from "lucide-react";
import { api } from "../lib/api";
import { toast } from "sonner";

interface Application {
  id: string;
  project_id: number;
  position_id: string;
  candidate_id: number;
  status: "pending" | "accepted" | "rejected";
  message: string;
  decided_by: number | null;
  decided_at: string | null;
  created_at: string;
  position?: {
    title: string;
    required_skills: string[];
  };
  project?: {
    name: string;
  };
}

export function MyApplications() {
  const [applications, setApplications] = useState<Application[]>([]);
  const [loading, setLoading] = useState(true);
  const [filter, setFilter] = useState<"all" | "pending" | "accepted" | "rejected">("all");

  useEffect(() => {
    loadMyApplications();
  }, []);

  const loadMyApplications = async () => {
    try {
      setLoading(true);
      const data = await api.getMyApplications();
      const items = Array.isArray(data?.items) ? data.items : Array.isArray(data) ? data : [];
      setApplications(items);
    } catch (error: any) {
      console.error("Failed to load my applications:", error);
      toast.error("Ошибка загрузки заявок");
    } finally {
      setLoading(false);
    }
  };

  const filteredApplications = applications.filter((app) =>
    filter === "all" ? true : app.status === filter
  );

  const getStatusColor = (status: string) => {
    switch (status) {
      case "pending":
        return "text-yellow-600 bg-yellow-50";
      case "accepted":
        return "text-green-600 bg-green-50";
      case "rejected":
        return "text-red-600 bg-red-50";
      default:
        return "text-gray-600 bg-gray-50";
    }
  };

  const getStatusIcon = (status: string) => {
    switch (status) {
      case "pending":
        return <Clock className="w-5 h-5" />;
      case "accepted":
        return <CheckCircle className="w-5 h-5" />;
      case "rejected":
        return <XCircle className="w-5 h-5" />;
      default:
        return <Clock className="w-5 h-5" />;
    }
  };

  const getStatusLabel = (status: string) => {
    switch (status) {
      case "pending":
        return "На рассмотрении";
      case "accepted":
        return "Одобрена";
      case "rejected":
        return "Отклонена";
      default:
        return status;
    }
  };

  if (loading) {
    return (
      <div className="py-20 text-center">
        <div className="inline-block animate-spin rounded-full h-12 w-12 border-b-2 border-primary"></div>
        <p className="mt-4 text-muted-foreground">Загрузка заявок...</p>
      </div>
    );
  }

  return (
    <div className="py-12">
      <div className="max-w-5xl mx-auto px-4 sm:px-6 lg:px-8">
        {/* Header */}
        <div className="mb-8">
          <h1 className="text-3xl md:text-4xl font-bold text-foreground mb-4">
            Мои заявки
          </h1>
          <p className="text-lg text-muted-foreground">
            Отслеживайте статус своих заявок на позиции
          </p>
        </div>

        {/* Stats */}
        <div className="grid grid-cols-2 md:grid-cols-4 gap-4 mb-8">
          <div className="bg-white rounded-lg border border-border p-4">
            <div className="text-2xl font-bold text-foreground">{applications.length}</div>
            <div className="text-sm text-muted-foreground">Всего заявок</div>
          </div>
          <div className="bg-yellow-50 rounded-lg border border-yellow-200 p-4">
            <div className="text-2xl font-bold text-yellow-600">
              {applications.filter((a) => a.status === "pending").length}
            </div>
            <div className="text-sm text-yellow-700">На рассмотрении</div>
          </div>
          <div className="bg-green-50 rounded-lg border border-green-200 p-4">
            <div className="text-2xl font-bold text-green-600">
              {applications.filter((a) => a.status === "accepted").length}
            </div>
            <div className="text-sm text-green-700">Одобрено</div>
          </div>
          <div className="bg-red-50 rounded-lg border border-red-200 p-4">
            <div className="text-2xl font-bold text-red-600">
              {applications.filter((a) => a.status === "rejected").length}
            </div>
            <div className="text-sm text-red-700">Отклонено</div>
          </div>
        </div>

        {/* Filters */}
        <div className="mb-6 flex space-x-2">
          <button
            onClick={() => setFilter("all")}
            className={`px-4 py-2 rounded-lg transition-colors ${
              filter === "all"
                ? "bg-primary text-white"
                : "bg-white border border-border hover:bg-secondary"
            }`}
          >
            Все
          </button>
          <button
            onClick={() => setFilter("pending")}
            className={`px-4 py-2 rounded-lg transition-colors ${
              filter === "pending"
                ? "bg-primary text-white"
                : "bg-white border border-border hover:bg-secondary"
            }`}
          >
            На рассмотрении
          </button>
          <button
            onClick={() => setFilter("accepted")}
            className={`px-4 py-2 rounded-lg transition-colors ${
              filter === "accepted"
                ? "bg-primary text-white"
                : "bg-white border border-border hover:bg-secondary"
            }`}
          >
            Одобренные
          </button>
          <button
            onClick={() => setFilter("rejected")}
            className={`px-4 py-2 rounded-lg transition-colors ${
              filter === "rejected"
                ? "bg-primary text-white"
                : "bg-white border border-border hover:bg-secondary"
            }`}
          >
            Отклоненные
          </button>
        </div>

        {/* Applications List */}
        {filteredApplications.length === 0 ? (
          <div className="text-center py-12 bg-white rounded-xl border border-border">
            <div className="w-16 h-16 bg-muted rounded-full flex items-center justify-center mx-auto mb-4">
              <Briefcase className="w-8 h-8 text-muted-foreground" />
            </div>
            <h3 className="text-xl font-semibold mb-2">Заявок нет</h3>
            <p className="text-muted-foreground mb-4">
              {filter === "all"
                ? "Вы еще не подавали заявок на позиции"
                : `Нет заявок со статусом "${getStatusLabel(filter)}"`}
            </p>
            <Link
              to="/positions"
              className="inline-block px-6 py-3 bg-primary text-white rounded-lg hover:bg-accent transition-colors"
            >
              Найти позиции
            </Link>
          </div>
        ) : (
          <div className="space-y-4">
            {filteredApplications.map((application) => (
              <div
                key={application.id}
                className="bg-white rounded-xl border border-border overflow-hidden hover:shadow-md transition-shadow"
              >
                <div className="p-6">
                  <div className="flex items-start justify-between mb-4">
                    <div className="flex-1">
                      <Link
                        to={`/projects/${application.project_id}`}
                        className="text-xl font-semibold hover:text-primary transition-colors"
                      >
                        {application.position?.title || "Позиция"}
                      </Link>
                      <div className="text-muted-foreground mt-1">
                        {application.project?.name || `Project #${application.project_id}`}
                      </div>
                    </div>
                    <div
                      className={`flex items-center space-x-2 px-4 py-2 rounded-full ${getStatusColor(
                        application.status
                      )}`}
                    >
                      {getStatusIcon(application.status)}
                      <span className="font-medium">{getStatusLabel(application.status)}</span>
                    </div>
                  </div>

                  {application.position?.required_skills && (
                    <div className="flex flex-wrap gap-2 mb-4">
                      {application.position.required_skills.map((skill) => (
                        <span
                          key={skill}
                          className="px-3 py-1 bg-secondary text-secondary-foreground text-sm rounded-full"
                        >
                          {skill}
                        </span>
                      ))}
                    </div>
                  )}

                  <div className="flex items-center space-x-1 text-sm text-muted-foreground">
                    <Calendar className="w-4 h-4" />
                    <span>Подана {new Date(application.created_at).toLocaleDateString("ru-RU")}</span>
                  </div>

                  {application.decided_at && (
                    <div className="mt-2 text-sm text-muted-foreground">
                      Решение принято {new Date(application.decided_at).toLocaleDateString("ru-RU")}
                    </div>
                  )}
                </div>

                {application.message && (
                  <div className="px-6 pb-6">
                    <div className="p-4 bg-secondary/50 rounded-lg">
                      <p className="text-sm font-medium text-muted-foreground mb-1">
                        Ваше сопроводительное письмо:
                      </p>
                      <p className="text-foreground">{application.message}</p>
                    </div>
                  </div>
                )}
              </div>
            ))}
          </div>
        )}
      </div>
    </div>
  );
}
