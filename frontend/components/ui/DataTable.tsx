import React from 'react';
import { cn } from '@/lib/utils';

export interface Column<T> {
  header: string;
  accessor: (row: T) => React.ReactNode;
  className?: string;
}

interface DataTableProps<T> {
  columns: Column<T>[];
  data: T[];
  emptyMessage?: string;
  onRowClick?: (row: T) => void;
  className?: string;
}

export function DataTable<T>({
  columns,
  data,
  emptyMessage = 'No records found.',
  onRowClick,
  className,
}: DataTableProps<T>) {
  return (
    <div className={cn('w-full overflow-x-auto border border-industrial-700 rounded bg-industrial-900', className)}>
      <table className="w-full text-left text-xs font-sans">
        <thead className="bg-industrial-850 border-b border-industrial-700 text-industrial-300 font-mono uppercase tracking-wider">
          <tr>
            {columns.map((col, i) => (
              <th key={i} className={cn('py-2.5 px-4 font-semibold', col.className)}>
                {col.header}
              </th>
            ))}
          </tr>
        </thead>
        <tbody className="divide-y divide-industrial-800">
          {data.length === 0 ? (
            <tr>
              <td colSpan={columns.length} className="py-8 text-center text-industrial-400 font-mono">
                {emptyMessage}
              </td>
            </tr>
          ) : (
            data.map((row, rowIndex) => (
              <tr
                key={rowIndex}
                onClick={() => onRowClick && onRowClick(row)}
                className={cn(
                  'hover:bg-industrial-800/50 transition-colors',
                  onRowClick && 'cursor-pointer'
                )}
              >
                {columns.map((col, colIndex) => (
                  <td key={colIndex} className={cn('py-3 px-4 text-industrial-200', col.className)}>
                    {col.accessor(row)}
                  </td>
                ))}
              </tr>
            ))
          )}
        </tbody>
      </table>
    </div>
  );
}
