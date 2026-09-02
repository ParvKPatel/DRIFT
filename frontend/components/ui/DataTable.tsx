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
    <div className={cn('w-full overflow-x-auto border border-industrial-800 rounded-sm bg-transparent', className)}>
      <table className="w-full text-left text-xs font-sans">
        <thead className="bg-industrial-900 border-b border-industrial-800 text-industrial-500 font-sans font-bold uppercase tracking-wider">
          <tr>
            {columns.map((col, i) => (
              <th key={i} className={cn('py-2.5 px-4', col.className)}>
                {col.header}
              </th>
            ))}
          </tr>
        </thead>
        <tbody className="divide-y divide-industrial-800">
          {data.length === 0 ? (
            <tr>
              <td colSpan={columns.length} className="py-8 text-center text-industrial-500 font-sans">
                {emptyMessage}
              </td>
            </tr>
          ) : (
            data.map((row, rowIndex) => (
              <tr
                key={rowIndex}
                onClick={() => onRowClick && onRowClick(row)}
                className={cn(
                  'hover:bg-industrial-900 transition-colors',
                  onRowClick && 'cursor-pointer'
                )}
              >
                {columns.map((col, colIndex) => (
                  <td key={colIndex} className={cn('py-3 px-4 text-industrial-100', col.className)}>
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
