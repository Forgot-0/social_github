import { useState, useRef } from 'react';
import { Dialog, DialogContent, DialogDescription, DialogFooter, DialogHeader, DialogTitle } from './ui/dialog';
import { Button } from './ui/button';
import { Avatar, AvatarFallback, AvatarImage } from './ui/avatar';
import { Loader2, Upload } from 'lucide-react';
import { toast } from 'sonner';
import { useGetAvatarPresignUrlMutation, useUploadAvatarCompleteMutation } from '../../api/hooks/useProfiles';

interface AvatarUploadDialogProps {
  open: boolean;
  onOpenChange: (open: boolean) => void;
  currentAvatarUrl?: string;
  displayName: string;
}

export function AvatarUploadDialog({ open, onOpenChange, currentAvatarUrl, displayName }: AvatarUploadDialogProps) {
  const [selectedFile, setSelectedFile] = useState<File | null>(null);
  const [previewUrl, setPreviewUrl] = useState<string | null>(null);
  const [uploading, setUploading] = useState(false);
  const fileInputRef = useRef<HTMLInputElement>(null);

  const getPresignUrlMutation = useGetAvatarPresignUrlMutation();
  const uploadCompleteMutation = useUploadAvatarCompleteMutation();

  const handleFileSelect = (e: React.ChangeEvent<HTMLInputElement>) => {
    const file = e.target.files?.[0];
    if (!file) return;

    // Validate file type
    if (!file.type.startsWith('image/')) {
      toast.error('Пожалуйста, выберите изображение');
      return;
    }

    // Validate file size (max 5MB)
    if (file.size > 5 * 1024 * 1024) {
      toast.error('Размер файла не должен превышать 5MB');
      return;
    }

    setSelectedFile(file);

    // Create preview
    const reader = new FileReader();
    reader.onloadend = () => {
      setPreviewUrl(reader.result as string);
    };
    reader.readAsDataURL(file);
  };

  const handleUpload = async () => {
    if (!selectedFile) return;

    setUploading(true);
    try {
      // Step 1: Get presigned URL
      const presignData = await getPresignUrlMutation.mutateAsync({
        filename: selectedFile.name,
        size: selectedFile.size,
        content_type: selectedFile.type,
      });

      // Step 2: Upload file to S3
      const formData = new FormData();
      Object.entries(presignData.fields).forEach(([key, value]) => {
        formData.append(key, value);
      });
      formData.append('file', selectedFile);

      const uploadResponse = await fetch(presignData.url, {
        method: 'POST',
        body: formData,
      });

      if (!uploadResponse.ok) {
        throw new Error('Ошибка при загрузке файла');
      }

      // Step 3: Notify backend upload is complete
      await uploadCompleteMutation.mutateAsync({
        key_base: presignData.key_base,
        size: selectedFile.size,
        content_type: selectedFile.type,
      });

      toast.success('Аватар успешно обновлен!');
      setSelectedFile(null);
      setPreviewUrl(null);
      onOpenChange(false);
    } catch (error: any) {
      toast.error('Ошибка при загрузке аватара', {
        description: error?.message || 'Попробуйте позже',
      });
    } finally {
      setUploading(false);
    }
  };

  const handleClose = () => {
    setSelectedFile(null);
    setPreviewUrl(null);
    onOpenChange(false);
  };

  return (
    <Dialog open={open} onOpenChange={handleClose}>
      <DialogContent>
        <DialogHeader>
          <DialogTitle>Загрузить аватар</DialogTitle>
          <DialogDescription>
            Выберите изображение для вашего профиля (макс. 5MB)
          </DialogDescription>
        </DialogHeader>

        <div className="flex flex-col items-center gap-6 py-4">
          <Avatar className="w-32 h-32">
            <AvatarImage src={previewUrl || currentAvatarUrl} alt={displayName} />
            <AvatarFallback className="text-4xl">{displayName[0]?.toUpperCase()}</AvatarFallback>
          </Avatar>

          <input
            ref={fileInputRef}
            type="file"
            accept="image/*"
            onChange={handleFileSelect}
            className="hidden"
          />

          <Button
            variant="outline"
            onClick={() => fileInputRef.current?.click()}
            disabled={uploading}
            className="w-full"
          >
            <Upload className="w-4 h-4 mr-2" />
            Выбрать изображение
          </Button>

          {selectedFile && (
            <p className="text-sm text-muted-foreground">
              Выбран файл: {selectedFile.name} ({(selectedFile.size / 1024).toFixed(2)} KB)
            </p>
          )}
        </div>

        <DialogFooter>
          <Button variant="outline" onClick={handleClose} disabled={uploading}>
            Отмена
          </Button>
          <Button onClick={handleUpload} disabled={!selectedFile || uploading}>
            {uploading ? (
              <>
                <Loader2 className="w-4 h-4 mr-2 animate-spin" />
                Загрузка...
              </>
            ) : (
              'Загрузить'
            )}
          </Button>
        </DialogFooter>
      </DialogContent>
    </Dialog>
  );
}
