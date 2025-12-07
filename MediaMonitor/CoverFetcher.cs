using System;
using System.IO;
using System.Threading.Tasks;
using WinRT;
using Windows.Storage.Streams;

namespace NowMediaMonitor
{
    public static class CoverFetcher
    {
        private static readonly string OutputDir = Path.Combine(
            Directory.GetParent(AppDomain.CurrentDomain.BaseDirectory).Parent.Parent.Parent.Parent.FullName,
            "songinfo"
        );

        public static async Task<bool> SaveCover(
            Windows.Media.Control.GlobalSystemMediaTransportControlsSessionMediaProperties mediaInfo,
            CurrentMediaState state)
        {
            if (mediaInfo.Thumbnail == null)
                return false;

            try
            {
                // Создаем директорию, если её нет
                Directory.CreateDirectory(OutputDir);

                var coverPath = Path.Combine(OutputDir, "cover.png");
                var stream = await mediaInfo.Thumbnail.OpenReadAsync();

                using var reader = new DataReader(stream);
                await reader.LoadAsync((uint)stream.Size);
                byte[] bytes = new byte[stream.Size];
                reader.ReadBytes(bytes);

                File.WriteAllBytes(coverPath, bytes);
                state.CoverPath = coverPath;

                // Не выводим в консоль для снижения нагрузки
                return true;
            }
            catch
            {
                // Игнорируем ошибки для снижения нагрузки
                return false;
            }
        }
    }
}
